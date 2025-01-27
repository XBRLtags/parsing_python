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
from taxonomy_parser import parse_taxonomy  # Assumes taxonomy_parser.py is in the same directory


class TaxonomyViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XBRL Taxonomy Viewer")
        self.setGeometry(100, 100, 1200, 800)
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

        self.setup_concepts_tab(self.tab_concepts)
        self.setup_hierarchical_tab(self.tab_dimensions, "Dimensions")
        self.setup_hierarchical_tab(self.tab_presentation, "Presentation Relationships")
        self.setup_formula_tab(self.tab_formulas)

        self.tabs.addTab(self.tab_concepts, "Concepts")
        self.tabs.addTab(self.tab_dimensions, "Dimensions")
        self.tabs.addTab(self.tab_presentation, "Presentation")
        self.tabs.addTab(self.tab_formulas, "Formulas")
        main_layout.addWidget(self.tabs)

    def setup_concepts_tab(self, tab):
        """Configure the Concepts tab."""
        tab.setColumnCount(7)
        tab.setHeaderLabels(["QName", "Name", "Type", "Substitution Group", "Period Type", "Balance", "Abstract"])

    def setup_hierarchical_tab(self, tab, header_text):
        """Configure a hierarchical tab (e.g., Dimensions or Presentation Relationships)."""
        tab.setColumnCount(1)
        tab.setHeaderLabels([header_text])

    def setup_formula_tab(self, tab):
        """Configure the Formulas tab."""
        tab.setColumnCount(4)
        tab.setHeaderLabels(["Formula Object", "Label", "Expression", "Children"])

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
            taxonomy_data = parse_taxonomy(file_path)

            # Populate tabs
            self.populate_concepts(self.tab_concepts, taxonomy_data.get("concepts", {}))
            self.populate_hierarchical(self.tab_dimensions, taxonomy_data.get("dimensions", {}))
            self.populate_hierarchical(self.tab_presentation, taxonomy_data.get("presentation_relationships", {}))
            self.populate_formulas(self.tab_formulas, taxonomy_data.get("formulas", {}))

            self.statusBar().showMessage("Taxonomy loaded successfully.", 5000)

        except Exception as e:
            self.statusBar().showMessage(f"Error loading taxonomy: {e}", 5000)
            print(f"Error loading taxonomy: {e}")

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
        """Populate a hierarchical tab with parent-child relationships."""
        tree.clear()
        if not relationships or not isinstance(relationships, dict):
            QTreeWidgetItem(tree, ["No valid data found"])
            return

        def add_items(parent_item, data):
            for parent, details in data.items():
                parent_node = QTreeWidgetItem([parent])
                if parent_item is None:
                    tree.addTopLevelItem(parent_node)
                else:
                    parent_item.addChild(parent_node)

                for child in details.get("children", []):
                    if isinstance(child, dict) and "name" in child:
                        child_node = QTreeWidgetItem([child["name"]])
                        parent_node.addChild(child_node)

        add_items(None, relationships)

    def populate_formulas(self, tree, formulas):
        """Populate the Formulas tab."""
        tree.clear()
        if not formulas:
            QTreeWidgetItem(tree, ["No formulas found"])
            return

        def add_items(parent_item, formula_data):
            for formula_name, details in (formula_data.items() if isinstance(formula_data, dict) else []):
                parent_node = QTreeWidgetItem([
                    formula_name,
                    details.get("label", ""),
                    details.get("expression", ""),
                    f"{len(details.get('children', []))} children",
                    str(details.get("bind_as_sequence", "")),
                ])
                if parent_item is None:
                    tree.addTopLevelItem(parent_node)
                else:
                    parent_item.addChild(parent_node)

                # Process children
                children = details.get("children", [])
                for child in children:
                    child_node = QTreeWidgetItem([
                        child.get("type", ""),
                        child.get("label", ""),
                        child.get("expression", ""),
                        f"{len(child.get('children', []))} children",
                    ])
                    parent_node.addChild(child_node)
                    add_items(child_node, child)

        add_items(None, formulas)



def main():
    app = QApplication(sys.argv)
    viewer = TaxonomyViewer()
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
