#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   data.py
@Contact :   huanghoward@foxmail.com
@Modify Time :    2021/6/25 14:50
------------
"""
import networkx as nx
import pandas as pd




class DAG(nx.DiGraph):
    """
    inherit class nx.DiGraph
    """

    def __init__(self, incoming_graph_data=None):
        super(DAG, self).__init__(incoming_graph_data)
        cycle = self._check_cycle()
        if cycle:
            out_str = "Cycles are not allowed in a DAG."
            out_str += "\nEdges indicating the path taken for a loop: "
            out_str += "".join([f"({u},{v}) " for (u, v) in cycle])
            raise ValueError(out_str)

    def _check_cycle(self):
        try:
            cycles = list(nx.find_cycle(self))
        except nx.NetworkXNoCycle:
            return False
        else:
            return cycles

    def score(self, score_method, data: pd.DataFrame, detail=False):
        score_dict = {}
        score_list = []
        for node in self.nodes:
            parents = list(self.predecessors(node))
            s = score_method(data)
            local_score = s.local_score(node, parents)
            score_list.append(local_score)
            if detail:
                score_dict[node] = local_score
        if detail:
            return sum(score_list), score_dict
        return sum(score_list) - 10e10

    def to_excel(self, path: str):
        edge_list = self.edges
        edges_data = pd.DataFrame(columns=['source node', 'target node'])
        for edge_pair in edge_list:
            edges_data.loc[edges_data.shape[0]] = {'source node': edge_pair[0], 'target node': edge_pair[1]}
        edges_data.to_excel(path)
        return None

    def __sub__(self, other):
        """
        Use structure Hamming Distance (SHD) to subtract.
        SHD = FP + FN
        FP: The number of edges discovered in the learned graph that do not exist in the true graph(other)
        FN: The number of direct independence discovered in the learned graph that do not exist in the true graph.
        :param other:
        :return:
        """
        if isinstance(self, type(other)):
            FP = len(set(self.edges) - set(other.edges))
            FN = len(set(other.edges) - set(self.edges))
            return FP + FN

        else:
            raise ValueError("cannot subtract DAG instance with other instance")

if __name__ == '__main__':
    d1 = DAG()
    d1.add_edge('a','b')
    d1.add_edge('c', 'b')
    d2 = DAG()
    d2.add_edge('a', 'b')
    d2.add_edge('b', 'c')
    print(d1-d2)



