from arelle.Cntlr import Cntlr


def parse_concepts(model_xbrl):
    """
    Extract concepts from the XBRL model.
    """
    print("\nExtracting Concepts...")
    concepts = {
        str(qname): {
            "name": concept.name,
            "type": concept.typeQname.localName if concept.typeQname else None,
            "substitution_group": concept.substitutionGroupQname.localName if concept.substitutionGroupQname else None,
            "period_type": concept.periodType,
            "balance": concept.balance,
            "abstract": concept.isAbstract,
        }
        for qname, concept in model_xbrl.qnameConcepts.items()
    }
    # print(f"Extracted {len(concepts)} concepts.")
    return concepts
