import xml.etree.ElementTree as ET

# Define your expected path in terms of methods to be fully covered
expected_methods = {
    'SortedListInsert$List': ['insert']
}

def parse_jacoco_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    coverage = {}
    
    # Iterate over each package in the report
    for package in root.findall('package'):
        package_name = package.get('name')
        for clazz in package.findall('class'):
            class_name = clazz.get('name').replace('/', '.')
            for method in clazz.findall('method'):
                method_name = method.get('name')
                # Get branch counter information for this method
                branch_counter = None
                for counter in method.findall('counter'):
                    if counter.get('type') == 'BRANCH':
                        branch_counter = {
                            'covered': int(counter.get('covered')),
                            'missed': int(counter.get('missed'))
                        }
                key = f"{class_name}#{method_name}"
                coverage[key] = branch_counter
    return coverage

def check_coverage(coverage, expected):
    all_passed = True
    for class_name, methods in expected.items():
        for method in methods:
            key = f"{class_name}#{method}"
            if key in coverage:
                counter = coverage[key]
                if counter['missed'] != 0:
                    print(f"Method {key} is not fully covered: missed {counter['missed']} branches")
                    all_passed = False
                else:
                    print(f"Method {key} is fully covered.")
            else:
                print(f"Method {key} not found in coverage report!")
                all_passed = False
    return all_passed

if __name__ == '__main__':
    xml_path = 'jacoco.xml'
    coverage = parse_jacoco_xml(xml_path)
    if check_coverage(coverage, expected_methods):
        print("Expected execution path is fully covered!")
    else:
        print("Coverage did not match the expected execution path.")
        exit(1)
