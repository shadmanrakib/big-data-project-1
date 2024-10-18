if result:
        print(f"Disease Name: {result['name']}")

        treats_drugs = set()
        palliates_drugs = set()
        anatomy_names = set()
        gene_names = set()

        for relation in result['related_nodes']:
            related_kind = relation['related_node']['kind']
            related_name = relation['related_node']['name']
            relation_type = relation['relation_type']

            if related_kind == 'Compound':
                if relation_type == 'CtD':  # Treats
                    treats_drugs.add(related_name)
                elif relation_type == 'CpD':  # Palliates
                    palliates_drugs.add(related_name)
            elif related_kind == 'Anatomy':
                anatomy_names.add(related_name)
            elif related_kind == 'Gene':
                gene_names.add(related_name)

        # Output the results
        print(f"\nDrugs:")
        print(f"Treats: {', '.join(treats_drugs) if treats_drugs else 'None'}")
        print(f"Palliates: {', '.join(palliates_drugs)}")

        print(f"\nAnatomy: {', '.join(anatomy_names)}")
        
        print(f"\nAssociated Genes: {', '.join(gene_names)}")
        
    else:
        print("No results found.")