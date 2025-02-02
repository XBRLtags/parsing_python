from collections import OrderedDict
from arelle import XbrlConst

def parse_calculations(model_xbrl):
    """
    Extracts calculation (summation-item) relationships from the XBRL taxonomy.
    Returns a hierarchical dictionary structured by roles.
    """
    calculation_arcroles = [
        "http://www.xbrl.org/2003/arcrole/summation-item",
        "https://xbrl.org/2023/arcrole/summation-item"
    ]

    # Dictionary to store calculations grouped by roles
    calculation_hierarchy = OrderedDict()

    for arcrole in calculation_arcroles:
        relationship_set = model_xbrl.relationshipSet(arcrole)
        if not relationship_set or not relationship_set.modelRelationships:
            continue

        # Group by roles
        for role in sorted(set(rel.linkrole for rel in relationship_set.modelRelationships)):
            role_uri = model_xbrl.roleTypeDefinition(role) or role  # Get the role name
            role_name = f"[{role.split('/')[-1]}] {role_uri}"

            role_hierarchy = OrderedDict()
            all_relationships = OrderedDict()
            all_parents = set()
            all_children = set()

            def get_concept_name(concept):
                """ Retrieve the QName local name for a concept """
                if concept is not None and hasattr(concept, "qname") and concept.qname:
                    return concept.qname.localName
                return None  # Return None if concept is invalid

            # Step 1: Extract relationships
            for rel in relationship_set.modelRelationships:
                if rel.linkrole != role:
                    continue  # Only process the current role

                from_concept = rel.fromModelObject
                to_concept = rel.toModelObject
                weight = getattr(rel, "weight", None)

                from_name = get_concept_name(from_concept)
                to_name = get_concept_name(to_concept)

                if from_name and to_name:
                    if from_name not in all_relationships:
                        all_relationships[from_name] = {"children": OrderedDict(), "weight": None}

                    all_relationships[from_name]["children"][to_name] = {"children": OrderedDict(), "weight": weight}

                    # Track parent and child nodes
                    all_parents.add(from_name)
                    all_children.add(to_name)

            # Step 2: Identify Root Nodes
            root_nodes = all_parents - all_children  # Find parents that are never children

            # Step 3: Assign role as enforced parent if no explicit root exists
            if not root_nodes:
                role_hierarchy[role_name] = {"children": all_relationships, "weight": None}
            else:
                for root in root_nodes:
                    if root in all_relationships:
                        role_hierarchy[root] = all_relationships[root]

            # Store under role-based structure
            calculation_hierarchy[role_name] = role_hierarchy

    return calculation_hierarchy
