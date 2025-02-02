# Compatibility Patch for imp in Python 3.12+
try:
    import imp
except ImportError:
    import importlib.util

    class imp:
        @staticmethod
        def find_module(name, path=None):
            spec = importlib.util.find_spec(name, path)
            if spec is None:
                raise ImportError(f"No module named {name}")
            return None, spec.origin, ("", "", None)

        @staticmethod
        def load_module(name, file, pathname, description):
            spec = importlib.util.spec_from_file_location(name, pathname)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

# Force inject the patched `imp` module into `sys.modules`
import sys
sys.modules["imp"] = imp

# Compatibility Patch for collections.abc in Python 3.10+
import collections
if not hasattr(collections, "MutableSet"):
    from collections.abc import MutableSet
    collections.MutableSet = MutableSet

if not hasattr(collections, "MutableMapping"):
    from collections.abc import MutableMapping
    collections.MutableMapping = MutableMapping

# Import GUI and taxonomy processing dependencies
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QTabWidget, QWidget, QFileDialog, QHBoxLayout,
    QStatusBar
)
from arelle.Cntlr import Cntlr
from concept_parser import parse_concepts
from dimension_parser import parse_dimensions
from presentation_parser import parse_presentation
from formula_parser import parse_formulas
from calculation_parser import parse_calculations  

class TaxonomyViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XBRL Taxonomy Viewer")
        self.setGeometry(100, 100, 1400, 850)
        self.setStatusBar(QStatusBar())

        # Main layout
        main_layout = QVBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # File loader section
        file_loader_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Enter path to taxonomy file...")
        file_loader_layout.addWidget(QLabel("Taxonomy File:"))
        file_loader_layout.addWidget(self.file_path_input)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        file_loader_layout.addWidget(browse_button)

        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_taxonomy)
        file_loader_layout.addWidget(load_button)

        main_layout.addLayout(file_loader_layout)

        # Tabs for different data views
        self.tabs = QTabWidget()
        self.tab_concepts = QTreeWidget()
        self.tab_dimensions = QTreeWidget()
        self.tab_presentation = QTreeWidget()
        self.tab_formulas = QTreeWidget()
        self.tab_calculations = QTreeWidget()

        self.setup_concepts_tab(self.tab_concepts)
        self.setup_dimensions_tab(self.tab_dimensions)
        self.setup_presentation_tab(self.tab_presentation)
        self.setup_formula_tab(self.tab_formulas)
        self.setup_calculation_tab(self.tab_calculations)

        self.tabs.addTab(self.tab_concepts, "Concepts")
        self.tabs.addTab(self.tab_dimensions, "Dimensions")
        self.tabs.addTab(self.tab_presentation, "Presentation")
        self.tabs.addTab(self.tab_formulas, "Formulas")
        self.tabs.addTab(self.tab_calculations, "Calculation Relationships")
        main_layout.addWidget(self.tabs)

    def setup_concepts_tab(self, tab):
        """Configure the Concepts tab."""
        tab.setColumnCount(7)
        tab.setHeaderLabels(["QName", "Name", "Type", "Substitution Group", "Period Type", "Balance", "Abstract"])

    def setup_dimensions_tab(self, tab):
        """Configure the Dimensions tab with extra columns."""
        tab.setColumnCount(5)
        tab.setHeaderLabels(["QName", "Arcrole", "CntxElt", "Closed", "Usable"])

    def setup_presentation_tab(self, tab):
        """Configure the Presentation tab with additional metadata."""
        tab.setColumnCount(4)
        tab.setHeaderLabels(["QName", "Pref. Label", "Type", "References"])

    def setup_formula_tab(self, tab):
        """Configure the Formulas tab with all required columns."""
        tab.setColumnCount(7)  # Increase column count
        tab.setHeaderLabels([
            "Formula Object", "Label", "Cover", "Complement", "BindAsSequence", "Expression", "Value"
        ])

    def setup_calculation_tab(self, tab):
        """Configure the Calculation Relationships tab."""
        tab.setColumnCount(3)
        tab.setHeaderLabels(["QName", "Weight", "Balance"])

    def browse_file(self):
        """Open a file dialog to select a taxonomy file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Taxonomy File", "", "XBRL Files (*.xsd)")
        if file_path:
            self.file_path_input.setText(file_path)

    def load_taxonomy(self):
        """Load the taxonomy file and populate the GUI tabs."""
        file_path = self.file_path_input.text()
        if not file_path:
            self.statusBar().showMessage("Please specify a taxonomy file path.", 5000)
            return

        try:
            cntlr = Cntlr()
            model_xbrl = cntlr.modelManager.load(file_path)
            if not model_xbrl:
                raise Exception(f"Failed to load taxonomy: {file_path}")

            # Call separate parsers
            concepts = parse_concepts(model_xbrl)
            dimensions = parse_dimensions(model_xbrl)
            presentation = parse_presentation(model_xbrl)
            formulas = parse_formulas(model_xbrl)  # ✅ Debug This Step
            calculations = parse_calculations(model_xbrl)

            # ✅ Debugging Output for Formulas
            print("\n✅ DEBUG: Raw Output from parse_formulas():")
            import json
            print(json.dumps(formulas, indent=4))  # ✅ Ensure formulas is not empty

            if not formulas:
                raise Exception("⚠️ No formulas were parsed. Check parse_formulas().")

            # Populate tabs
            self.populate_concepts(self.tab_concepts, concepts)
            self.populate_hierarchical(self.tab_dimensions, dimensions)
            self.populate_hierarchical(self.tab_presentation, presentation)
            self.populate_formulas(self.tab_formulas, formulas)  # ✅ Ensure formulas is valid
            self.populate_calculations(self.tab_calculations, calculations)

            model_xbrl.close()
            self.statusBar().showMessage("Taxonomy loaded successfully.", 5000)

        except Exception as e:
            self.statusBar().showMessage(f"Error loading taxonomy: {e}", 5000)
            print(f"❌ ERROR: {e}")



    def populate_concepts(self, tree, concepts):
        """Populate the Concepts tab."""
        tree.clear()
        if not concepts:
            QTreeWidgetItem(tree, ["No concepts found"])
            return

        for qname, details in concepts.items():
            item = QTreeWidgetItem([
                qname,
                details.get("name", ""),
                details.get("type", ""),
                details.get("substitution_group", ""),
                details.get("period_type", ""),
                details.get("balance", ""),
                str(details.get("abstract", False))
            ])
            tree.addTopLevelItem(item)

    def populate_hierarchical(self, tree, relationships):
        """Populate hierarchical tabs (Dimensions & Presentation)."""
        tree.clear()
        if not relationships:
            QTreeWidgetItem(tree, ["No data available"])
            return

        def add_items(parent_item, data):
            for parent, details in data.items():
                parent_node = QTreeWidgetItem([parent])
                if parent_item is None:
                    tree.addTopLevelItem(parent_node)
                else:
                    parent_item.addChild(parent_node)

                for child in details.get("children", []):
                    child_node = QTreeWidgetItem([child["name"]])
                    parent_node.addChild(child_node)
                    add_items(child_node, {c["name"]: c for c in child.get("children", [])})

        add_items(None, relationships)

    

    def populate_formulas(self, tree, formulas):
        """Populate the Formulas tab with a hierarchical tree structure."""
        tree.clear()

        if not formulas:
            print("⚠️ WARNING: No formulas found. GUI will remain empty.")
            QTreeWidgetItem(tree, ["No formulas found"])
            return

        def add_items(parent_item, formula_dict):
            """Recursively add formula objects to the tree view."""
            for formula_obj, details in formula_dict.items():
                label_text = details.get("label", formula_obj)  # Use formula_obj if label is missing

                # **🌟 DEBUG: Print hierarchy before adding to GUI**
                print(f"📌 Adding to GUI: {formula_obj} under {parent_item.text(0) if parent_item else 'ROOT'}")

                # ✅ Create tree node
                item = QTreeWidgetItem([
                    formula_obj,  # Formula Object Name
                    label_text,  # The Label of the object
                    str(details.get("cover", "")),
                    str(details.get("complement", "")),
                    str(details.get("bindAsSequence", "")),
                    details.get("expression", ""),
                    details.get("value", ""),
                ])

                # ✅ Attach to Parent Correctly
                if parent_item:
                    parent_item.addChild(item)
                    item.setExpanded(False)  # ❌ Keep child nodes collapsed by default

                # ✅ Process Children Correctly
                children = details.get("children", {})
                if children:
                    print(f"🔽 {formula_obj} has {len(children)} children")  # Debugging Output
                    add_items(item, children)  # ✅ Attach child nodes correctly

        # ✅ Ensure only root-level formulas (assertionSets) are displayed
        for root_formula, formula_details in formulas.items():
            print(f"📌 Root formula in GUI: {root_formula}")  # Debugging Output

            # ✅ Fix: Ensure correct root structure
            root_details = formula_details.get(root_formula, formula_details)  # Ensure correct extraction
            root_item = QTreeWidgetItem(tree, [
                root_formula,
                root_details.get("label", root_formula),
                str(root_details.get("cover", "")),
                str(root_details.get("complement", "")),
                str(root_details.get("bindAsSequence", "")),
                root_details.get("expression", ""),
                root_details.get("value", ""),
            ])
            tree.addTopLevelItem(root_item)  # ✅ Only root-level formulas appear in UI
            root_item.setExpanded(False)  # ❌ Ensure all child nodes are collapsed

            # ✅ Attach children properly (Keep collapsed)
            children = root_details.get("children", {})
            if children:
                print(f"🔽 Root {root_formula} has {len(children)} children")  # Debugging Output
                add_items(root_item, children)  # ✅ Correctly attach child nodes

        tree.repaint()  # ✅ Force GUI refresh
        tree.update()  # ✅ Ensure GUI updates immediately



    def populate_calculations(self, tree, calculations):
        """Populate the Calculation Relationships tab in the GUI with hierarchical structure."""
        tree.clear()

        if not calculations:
            QTreeWidgetItem(tree, ["No calculations found"])
            return

        def add_items(parent_item, data):
            """Recursively adds calculation relationships to the tree widget."""
            for parent, details in data.items():
                weight = str(details.get("weight", ""))
                balance = details.get("balance", "")

                parent_node = QTreeWidgetItem([parent, weight, balance])

                if parent_item is None:
                    tree.addTopLevelItem(parent_node)
                else:
                    parent_item.addChild(parent_node)

                for child_name, child_details in details.get("children", {}).items():
                    add_items(parent_node, {child_name: child_details})

        # Add roles as the top-level items
        for role, role_data in calculations.items():
            role_item = QTreeWidgetItem([role, "", ""])  # Role name as top-level
            tree.addTopLevelItem(role_item)

            for parent, details in role_data.items():
                parent_node = QTreeWidgetItem([parent, str(details.get("weight", "")), details.get("balance", "")])
                role_item.addChild(parent_node)

                for child_name, child_details in details.get("children", {}).items():
                    add_items(parent_node, {child_name: child_details})



def main():
    app = QApplication(sys.argv)
    viewer = TaxonomyViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
