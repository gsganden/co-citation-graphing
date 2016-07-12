import sys
import re
import networkx as nx
import community
from networkx.readwrite import d3_js

data = sys.argv[1]
cite_threshold = int(sys.argv[2])
co_cite_threshold = int(sys.argv[3])

cite_counter = {}
co_cite_counter = {}
improperly_formatted_cites = []
redundant_cites = []

with open(data, 'r') as f:
    # Replace line breaks within a field with tabs before splitting by line
    data_fields = f.read().replace('\n   ', '\t').split('\n')

for field in data_fields:
    if field[:2] == "CR":  # Check that data field is a citation record
        cites = field[3:].split('\t')
        processed_cites = []
        for cite in cites:
            # Enforce consistent formatting
            cite_match = re.search(r'(\S+\s\S+)(,.*)', cite)
            if cite_match is None:
                improperly_formatted_cites.append(cite)
            else:
                name_split = cite_match.group(1).split()
                last_name = name_split[0].title()
                initials = (''.join([char for char in name_split[1]
                                     if re.search(r"[a-zA-Z]", char)])).upper()
                cite_id = last_name + ' ' + initials + cite_match.group(2)
                if cite_id in processed_cites:
                    redundant_cites.append(cite)
                else:
                    cite_counter[cite_id] = cite_counter.get(cite_id, 0) + 1
                    processed_cites.append(cite_id)
                    for processed_cite in processed_cites:
                        first_cite, second_cite = sorted([cite_id,
                                                          processed_cite])
                        co_cite_counter[(first_cite, second_cite)] =\
                            co_cite_counter.get((first_cite,
                                                 second_cite), 0) + 1
                    processed_cites.append(cite_id)

graph = nx.Graph()
num_edges = 0
full_cites = []  # Captures full citation information to display below graph

for cite_pair in co_cite_counter:
    if cite_counter[cite_pair[0]] >= cite_threshold\
            and cite_counter[cite_pair[1]] >= cite_threshold\
            and co_cite_counter[cite_pair] >= co_cite_threshold:
        graph.add_edge(cite_pair[0], cite_pair[1],
                       weight=co_cite_counter[cite_pair])
        for cite in cite_pair:
            if cite not in full_cites:
                full_cites.append(cite)
        num_edges += 1

partition = community.best_partition(graph)

for node in graph:
    graph.add_node(node, freq=cite_counter[node], group=str(partition[node]))

d3_js.export_d3_js(graph, files_dir='results', graphname='graph',
                   node_labels=True, group='group')

with open('results/graph.json', 'rb') as graph_json:
    fix = graph_json.read()
    for node in graph:
        try:
            fix = re.sub(str(node) + '"',
                         str(node) + '" , "nodeSize":' +
                         str(cite_counter[node]),
                         fix)
        except:
            print 'Error with %s' % node

with open('results/graph.json', 'w+') as graph_json:
    graph_json.write(fix)

with open('results/graph.html', 'a') as graph_html:
    for item in sorted(full_cites):
        graph_html.write('<p>' + str(item) + '</p>\n')

print 'Number of nodes: %d' % len(partition)
print 'Number of edges: %d' % num_edges
print 'Citations processed: %d' % sum(cite_counter.itervalues())
print 'Citations not processed: %d' % len(redundant_cites +
                                          improperly_formatted_cites)
if len(redundant_cites) > 0:
    print '\t Apparently redundant citations:'
    for cite in redundant_cites:
        print '\t\t' + cite
if len(improperly_formatted_cites) > 0:
    print '\t Improperly formatted citations:'
    for cite in improperly_formatted_cites:
        print '\t\t' + cite
