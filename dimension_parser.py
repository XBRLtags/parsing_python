from collections import defaultdict, OrderedDict
from arelle.ModelRelationshipSet import ModelRelationshipSet

def process_relationships(arcrole, relationship_set, elr):
    """
    Processes relationships for a given arcrole and builds a deep hierarchical structure.
    Captures missing parents & enforces proper ELR grouping.

    :param arcrole: The arcrole of the relationships to process.
    :param relationship_set: The set of relationships to process.
    :param elr: The Extended Link Role (ELR) grouping.
    :return: A dictionary representing the full hierarchy of relationships.
    """
    # print(f"\n📂 Processing Relationships for arcrole: {arcrole} in ELR: {elr}")
    hierarchy = OrderedDict()
    parent_child_map = defaultdict(lambda: {"abstract": False, "children": OrderedDict(), "parent": None})

    if relationship_set and relationship_set.modelRelationships:
        for rel in relationship_set.modelRelationships:
            parent = rel.fromModelObject
            child = rel.toModelObject

            # Validate parent and child
            if parent is None or child is None or not hasattr(parent, 'qname') or not hasattr(child, 'qname'):
                continue

            # Assign names: Parent gets `[role-XXXXXX]`, Child keeps original
            role_prefix = f"[{elr.split('/')[-1]}] "
            parent_name = role_prefix + parent.qname.localName
            child_name = child.qname.localName  # No role prefix for children

            # print(f"🔹 Relationship Found: {parent_name} → {child_name}")

            # Ensure parent exists in mapping
            if parent_name not in parent_child_map:
                parent_child_map[parent_name]["abstract"] = parent.isAbstract

            # Ensure child exists in mapping before assigning parent
            if child_name not in parent_child_map:
                parent_child_map[child_name] = {"abstract": child.isAbstract, "children": OrderedDict(), "parent": None}

            # Mark the child's parent explicitly
            parent_child_map[child_name]["parent"] = parent_name

            # Add child under the parent
            parent_child_map[parent_name]["children"][child_name] = parent_child_map[child_name]

    print("\n🔍 Parent-Child Mapping Table:")
    for parent, data in parent_child_map.items():
        # print(f"  🔺 {parent}: {len(data['children'])} children")
        for child in data["children"]:
            print(f"    └── {child}")

    # **Recursive Function to Build Full Hierarchy**
    def build_hierarchy(node_name, visited=None, depth=0):
        if visited is None:
            visited = set()
        if node_name in visited:  # Prevent cycles
            # print(f"⚠️ Cycle detected! Skipping {node_name}")
            return None
        visited.add(node_name)

        node_data = parent_child_map.get(node_name, {"abstract": False, "children": {}})
        
        node = {
            "name": node_name,
            "abstract": node_data["abstract"],
            "children": []
        }

        # ✅ Recursively build children hierarchy
        for child_name, child_data in node_data["children"].items():
            if child_name in parent_child_map:  # Ensure we process child if it has children
                # print(f"{'  ' * depth}↳ Recursing into child: {child_name}")
                child_hierarchy = build_hierarchy(child_name, visited, depth + 1)
                if child_hierarchy:
                    node["children"].append(child_hierarchy)

        visited.remove(node_name)
        return node

    # **Identify Root Nodes (Ensure Missing Parents Are Captured)**
    all_parents = set(parent_child_map.keys())
    all_children = {child for children in parent_child_map.values() for child in children["children"]}
    root_nodes = all_parents - all_children  # Find true root nodes

    if not root_nodes:
        # print(f"⚠️ No standalone root nodes found for arcrole {arcrole} in ELR {elr}. Using fallback strategy.")
        root_nodes = set(parent_child_map.keys())  # Use all available as fallback

    # print(f"🔍 Detected Root Nodes for {elr}: {root_nodes}")

    for root in root_nodes:
        hierarchy[root] = build_hierarchy(root)

    # print(f"📌 Processed {len(hierarchy)} root nodes for {arcrole} in {elr}.")

    # **🔍 Print full built hierarchy**
    # print("\n🧩 Built Hierarchy Structure:")
    for root, structure in hierarchy.items():
        print_hierarchy(structure)

    return hierarchy


def print_hierarchy(node, indent=0):
    """ Utility function to print the full hierarchy in a structured format. """
    #print(f"{'  ' * indent}- {node['name']}")
    for child in node["children"]:
        print_hierarchy(child, indent + 1)


def parse_dimensions(model_xbrl):
    """
    Parses dimension relationships in the XBRL taxonomy and captures their **full hierarchical structure**.

    :param model_xbrl: The loaded XBRL model.
    :return: A dictionary representing the full dimension relationships.
    """
    # print("\n📂 Processing Dimensions...")

    dim_arcroles = [
        "http://xbrl.org/int/dim/arcrole/hypercube-dimension",
        "http://xbrl.org/int/dim/arcrole/dimension-domain",
        "http://xbrl.org/int/dim/arcrole/domain-member",
    ]

    dimensions = OrderedDict()
    for arcrole in dim_arcroles:
        relationship_set = model_xbrl.relationshipSet(arcrole)
        if relationship_set and relationship_set.modelRelationships:
            all_elrs = relationship_set.linkRoleUris
            for elr in all_elrs:
                print(f"\n🛠 Processing ELR: {elr}")
                elr_relationship_set = model_xbrl.relationshipSet(arcrole, elr)
                arcrole_hierarchy = process_relationships(arcrole, elr_relationship_set, elr)
                dimensions.update(arcrole_hierarchy)
        else:
            print(f"⚠️ No relationship set found for arcrole {arcrole}")

    # print(f"\n✅ Parsed {len(dimensions)} root dimension nodes.")
    return dimensions
