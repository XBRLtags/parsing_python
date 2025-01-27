from arelle.Cntlr import Cntlr
from arelle.ModelFormulaObject import ModelVariable, ModelParameter, ModelVariableSetAssertion, ModelConsistencyAssertion
from arelle.ViewUtilFormulae import rootFormulaObjects


def process_relationships(arcrole, relationship_set):
    """
    Processes relationships for a given arcrole and builds a hierarchy.
    """
    print(f"\nProcessing Relationships for arcrole: {arcrole}")
    hierarchy = {}
    skipped_relationships = []

    if relationship_set and relationship_set.modelRelationships:
        total_relationships = len(relationship_set.modelRelationships)
        print(f"Number of Relationships for {arcrole}: {total_relationships}")

        for i, rel in enumerate(relationship_set.modelRelationships):
            parent = rel.fromModelObject
            child = rel.toModelObject

            # Check for missing or invalid parent/child
            if parent is None or child is None:
                skipped_relationships.append((parent, child, "Parent or child is None"))
                continue

            if not getattr(parent, 'qname', None) or not getattr(child, 'qname', None):
                skipped_relationships.append((parent, child, "Missing QName"))
                continue

            # Build hierarchy
            parent_name = str(parent.qname)
            child_name = str(child.qname)

            if parent_name not in hierarchy:
                hierarchy[parent_name] = {"abstract": parent.isAbstract, "children": []}

            if not any(c["name"] == child_name for c in hierarchy[parent_name]["children"]):
                hierarchy[parent_name]["children"].append({"name": child_name, "abstract": child.isAbstract})

        print(f"Processed {total_relationships} relationships.")

    else:
        print(f"No relationships found for arcrole {arcrole}.")

    print(f"Skipped Relationships for arcrole {arcrole}: {len(skipped_relationships)}")

    return hierarchy


def parse_formula(model_xbrl):
    """
    Parses formulas and their relationships, capturing hierarchy and children.
    """
    print("\nProcessing Formulas...")
    formula_hierarchy = {}

    # Retrieve root formula objects
    root_objects = rootFormulaObjects(model_xbrl)
    print(f"Found {len(root_objects)} root formula objects.")
    for root in root_objects:
        print(f"Root Formula Object: {root.localName}, Label: {root.xlinkLabel}")

    # Process relationships for formula arc roles
    formula_arcroles = [
        "http://xbrl.org/arcrole/2008/assertion-set",
        "http://xbrl.org/arcrole/2008/variable-set",
        "http://xbrl.org/arcrole/2008/variable-set-filter",
    ]

    def process_formula_object(obj, relationship_set, hierarchy, visited=None, depth=0, max_depth=100):
        """
        Recursive function to process formula objects and build their hierarchy.
        """
        if visited is None:
            visited = set()

        # Check for recursion limits
        if depth > max_depth:
            print(f"Max recursion depth reached for object: {obj.xlinkLabel}")
            return

        # Avoid cycles
        if obj in visited:
            return
        visited.add(obj)

        # Add object to the hierarchy
        obj_name = obj.xlinkLabel or str(obj.localName)
        if obj_name not in hierarchy:
            hierarchy[obj_name] = {
                "type": obj.localName,  # e.g., "assertionSet", "valueAssertion"
                "label": obj.xlinkLabel,
                "children": []
            }

        # Get children for the current object
        if relationship_set:
            for rel in relationship_set.fromModelObject(obj):
                child = rel.toModelObject
                if child is not None:
                    # Add child recursively
                    child_hierarchy = {}
                    process_formula_object(child, relationship_set, child_hierarchy, visited, depth + 1, max_depth)
                    hierarchy[obj_name]["children"].append(child_hierarchy)

        visited.remove(obj)

    # Process each root object to build the hierarchy
    for arcrole in formula_arcroles:
        print(f"\nProcessing Formula Relationships for arcrole: {arcrole}")
        relationship_set = model_xbrl.relationshipSet(arcrole)
        if relationship_set:
            for root in root_objects:
                if root.xlinkLabel not in formula_hierarchy:
                    formula_hierarchy[root.xlinkLabel] = {}
                process_formula_object(root, relationship_set, formula_hierarchy[root.xlinkLabel])
        else:
            print(f"No relationships found for arcrole: {arcrole}")

    print(f"\nProcessed {len(formula_hierarchy)} formula objects.")
    return formula_hierarchy


def parse_taxonomy(taxonomy_file):
    """
    Parses an XBRL taxonomy file and extracts concepts, presentation relationships, dimensions, and formulas.
    """
    cntlr = Cntlr()  # Initialize Arelle controller

    # Load the taxonomy
    model_xbrl = cntlr.modelManager.load(taxonomy_file)
    if not model_xbrl:
        raise Exception(f"Failed to load taxonomy: {taxonomy_file}")

    print("\nExtracting Concepts...")
    concepts = {}
    for qname, concept in model_xbrl.qnameConcepts.items():
        concepts[str(qname)] = {
            "name": concept.name,
            "type": concept.typeQname.localName if concept.typeQname else None,
            "substitution_group": concept.substitutionGroupQname.localName if concept.substitutionGroupQname else None,
            "period_type": concept.periodType,
            "balance": concept.balance,
            "abstract": concept.isAbstract,
        }
    print(f"Extracted {len(concepts)} concepts.")

    print("\nProcessing Presentation Relationships...")
    presentation_relationships = {}
    relationship_set = model_xbrl.relationshipSet("http://www.xbrl.org/2003/arcrole/parent-child")
    if relationship_set:
        presentation_relationships = process_relationships("http://www.xbrl.org/2003/arcrole/parent-child", relationship_set)
    else:
        print("No Presentation Relationships Found.")

    print("\nProcessing Dimensions...")
    dimensions = {}
    unified_dimensions = {}
    dim_arcroles = [
        "http://xbrl.org/int/dim/arcrole/hypercube-dimension",
        "http://xbrl.org/int/dim/arcrole/dimension-domain",
        "http://xbrl.org/int/dim/arcrole/domain-member",
    ]
    for arcrole in dim_arcroles:
        print(f"\nProcessing Dimension Relationships for arcrole: {arcrole}")
        relationship_set = model_xbrl.relationshipSet(arcrole)
        if relationship_set:
            dimensions[arcrole] = process_relationships(arcrole, relationship_set)
            # Merge into unified dimensions
            for parent, details in dimensions[arcrole].items():
                if parent not in unified_dimensions:
                    unified_dimensions[parent] = details
                else:
                    unified_dimensions[parent]["children"].extend(details["children"])
        else:
            print(f"No Relationships Found for Arcrole: {arcrole}")

    print("\nProcessing Formulas...")
    formulas = parse_formula(model_xbrl)

    model_xbrl.close()

    print("\nFinal Results:")
    print(f"- Concepts: {len(concepts)}")
    print(f"- Presentation Relationships: {len(presentation_relationships)} top-level nodes")
    print(f"- Dimensions: {len(unified_dimensions)} unique parents")
    print(f"- Formulas: {len(formulas)}")

    return {
        "concepts": concepts,
        "presentation_relationships": presentation_relationships,
        "dimensions": unified_dimensions,
        "formulas": formulas,
    }
