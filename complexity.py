#!/usr/bin/python

import csv

'''
{
    graph_name: {
        "graph_complexity" : "",
        "flow_complexity" : "",
        "components" : {
            component_name : {
                "component_complexity" : "",
                "transform_complexity" : ""
            }
        }
    }
}
'''

filename = 'complexity.txt'


def get_complexity(filename):

    raw_complexity_dict = {}
    with open(filename, 'r') as fp:
        for content in fp:
            if len(content.split()) >= 4:
                graph_name, graph_complexity, dummy, flow_complexity = content.split()[:4]
                try:
                    assert int(graph_complexity)
                except:
                    graph_complexity = 0
                try:
                    assert int(flow_complexity)
                except:
                    flow_complexity = 0
                raw_complexity_dict.setdefault(graph_name, {})
                raw_complexity_dict[graph_name]["graph_complexity"] = graph_complexity
                raw_complexity_dict[graph_name]["flow_complexity"]  = flow_complexity

            elif len(content.split()) == 3:
                component_name, component_complexity, transform_complexity = content.split()
                try:
                    assert int(component_complexity)
                except:
                    component_complexity = 0
                try:
                    assert int(transform_complexity)
                except:
                    transform_complexity = 0
                raw_complexity_dict[graph_name].setdefault('components', {})
                raw_complexity_dict[graph_name]['components'].setdefault(component_name, {})
                raw_complexity_dict[graph_name]['components'][component_name]["component_complexity"] = component_complexity
                raw_complexity_dict[graph_name]['components'][component_name]["transform_complexity"] = transform_complexity

    return raw_complexity_dict


def summarize_complexity(graphs):

    summary_complexity_list = []
    for graph in graphs:
        summary_complexity_dict = {}
        summary_complexity_dict['graph'] = graph
        summary_complexity_dict['graph_complexity_score'] = int(graphs[graph]['graph_complexity'])
        summary_complexity_dict['flow_complexity_score'] = int(graphs[graph]['flow_complexity'])

        total_components = 0
        component_complexity_count = 0
        transform_complexity_count = 0
        component_complexity_score = 0
        transform_complexity_score = 0

        for component in graphs[graph].get('components', {}):
            component_complexity = 0
            transform_complexity = 0
            total_components += 1

            component_complexity = int(graphs[graph]['components'][component]['component_complexity'])
            transform_complexity = int(graphs[graph]['components'][component]['transform_complexity'])

            component_complexity_score += component_complexity
            transform_complexity_score += transform_complexity

            if transform_complexity > 0:
                transform_complexity_count += 1

            if component_complexity > 0:
                component_complexity_count += 1

        summary_complexity_dict['transform_complexity_score'] = transform_complexity_score
        summary_complexity_dict['component_complexity_score'] = component_complexity_score
        summary_complexity_dict['transform_complexity_count'] = transform_complexity_count
        summary_complexity_dict['component_complexity_count'] = component_complexity_count
        summary_complexity_dict['total_components'] = total_components
        summary_complexity_list.append(summary_complexity_dict)

    return summary_complexity_list


def create_csv(summary):

    with open('complexity_summary.csv', mode='w') as complexity_summary_file:
        complexity_writer = csv.writer(complexity_summary_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        header = []
        header.append('GraphName')
        header.append('GraphScore')
        header.append('FlowScore')
        header.append('TransformScore')
        header.append('ComponentScore')
        header.append('TransformCount')
        header.append('ComponentCount')
        header.append('TotalComponents')
        complexity_writer.writerow(header)

        for entry in summary:
            each_row = []
            each_row.append(entry['graph'])
            each_row.append(entry['graph_complexity_score'])
            each_row.append(entry['flow_complexity_score'])
            each_row.append(entry['transform_complexity_score'])
            each_row.append(entry['component_complexity_score'])
            each_row.append(entry['transform_complexity_count'])
            each_row.append(entry['component_complexity_count'])
            each_row.append(entry['total_components'])

            complexity_writer.writerow(each_row)


summary = sorted(summarize_complexity(get_complexity(filename)), key=lambda x: x['graph_complexity_score'], reverse=True)
create_csv(summary)








