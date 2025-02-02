from arelle.Cntlr import Cntlr
from arelle.ModelRelationshipSet import ModelRelationshipSet


def process_relationships(arcrole, relationship_set):
    """
    Processes relationships for a given arcrole and builds a hierarchy.

    :param arcrole: The arcrole of the relationships to process.
    :param relationship_set: The set of relationships to process.
    :return: A dictionary representing the hierarchy of relationships.
    """
    # print(f"\nProcessing Relationships for arcrole: {arcrole}")
    hierarchy = {}
    skipped_relationships = []

    if relationship_set and relationship_set.modelRelationships:
        total_relationships = len(relationship_set.modelRelationships)
        # print(f"Number of Relationships for {arcrole}: {total_relationships}")

        # Parent-Child Map
        parent_child_map = {}
        for rel in relationship_set.modelRelationships:
            parent = rel.fromModelObject
            child = rel.toModelObject

            # Skip relationships with missing parents or children
            if parent is None or child is None:
                skipped_relationships.append((parent, child, "Parent or child is None"))
                continue

            # Ensure QNames are valid
            if not getattr(parent, 'qname', None) or not getattr(child, 'qname', None):
                skipped_relationships.append((parent, child, "Missing QName"))
                continue

            parent_name = str(parent.qname)
            child_name = str(child.qname)

            # Initialize parent node if not already present
            if parent_name not in parent_child_map:
                parent_child_map[parent_name] = {"abstract": parent.isAbstract, "children": []}

            # Add child to parent's children list
            if not any(c["name"] == child_name for c in parent_child_map[parent_name]["children"]):
                parent_child_map[parent_name]["children"].append({"name": child_name, "abstract": child.isAbstract})

        # Build hierarchy recursively
        def build_hierarchy(node_name, node_data):
            node = {
                "name": node_name,
                "abstract": node_data["abstract"],
                "children": []
            }
            for child in node_data["children"]:
                child_name = child["name"]
                if child_name in parent_child_map:
                    node["children"].append(build_hierarchy(child_name, parent_child_map[child_name]))
                else:
                    node["children"].append({"name": child_name, "abstract": child["abstract"], "children": []})
            return node

        # Identify root nodes (parents that are not children)
        root_nodes = set(parent_child_map.keys()) - {
            child["name"] for children in parent_child_map.values() for child in children["children"]
        }

        # Build hierarchy for each root node
        for root in root_nodes:
            hierarchy[root] = build_hierarchy(root, parent_child_map[root])

        # print(f"Processed {total_relationships - len(skipped_relationships)} relationships.")
    else:
        print(f"No relationships found for arcrole {arcrole}.")

    # print(f"Skipped {len(skipped_relationships)} relationships for arcrole {arcrole}.")
    return hierarchy


def parse_presentation(model_xbrl):
    """
    Extract presentation relationships and build a hierarchical structure.

    :param model_xbrl: The XBRL model object containing the taxonomy data.
    :return: A dictionary representing the hierarchical structure of presentation relationships.
    """
    print("\nProcessing Presentation Relationships...")
    presentation_arcrole = "http://www.xbrl.org/2003/arcrole/parent-child"
    relationship_set = model_xbrl.relationshipSet(presentation_arcrole)
    if relationship_set:
        return process_relationships(presentation_arcrole, relationship_set)
    else:
        print(f"No relationships found for arcrole: {presentation_arcrole}.")
        return {}
