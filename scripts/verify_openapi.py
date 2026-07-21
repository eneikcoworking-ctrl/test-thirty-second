#!/usr/bin/env python3
import sys
import yaml

def verify_openapi():
    try:
        with open("docs/openapi.yaml", "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: docs/openapi.yaml not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)

    print("Success: docs/openapi.yaml is valid YAML.")

    # Validate essential OpenAPI components
    if "openapi" not in spec:
        print("Error: Missing 'openapi' field.")
        sys.exit(1)

    # Check paths
    paths = spec.get("paths", {})
    required_paths = ["/notes", "/notes/{id}"]
    for rp in required_paths:
        if rp not in paths:
            print(f"Error: Missing path '{rp}'.")
            sys.exit(1)

    print("Success: Necessary paths exist.")

    # Check endpoints (methods)
    notes_methods = paths.get("/notes", {})
    if "get" not in notes_methods or "post" not in notes_methods:
        print("Error: '/notes' must have 'get' and 'post' methods.")
        sys.exit(1)

    note_by_id_methods = paths.get("/notes/{id}", {})
    if "get" not in note_by_id_methods or "put" not in note_by_id_methods or "delete" not in note_by_id_methods:
        print("Error: '/notes/{id}' must have 'get', 'put', and 'delete' methods.")
        sys.exit(1)

    print("Success: Endpoints for creating, reading, updating, and deleting notes are defined.")

    # Check Note Schema
    schemas = spec.get("components", {}).get("schemas", {})
    if "Note" not in schemas:
        print("Error: Missing 'Note' schema.")
        sys.exit(1)

    note_schema = schemas["Note"]
    properties = note_schema.get("properties", {})
    required_fields = ["title", "body", "createdAt", "updatedAt", "ownerId"]

    for field in required_fields:
        if field not in properties:
            print(f"Error: 'Note' schema is missing the required field '{field}'.")
            sys.exit(1)

    print("Success: 'Note' schema contains all mandatory fields (title, body, timestamps, and owner ID).")
    print("All contract validation checks passed successfully.")

if __name__ == "__main__":
    verify_openapi()
