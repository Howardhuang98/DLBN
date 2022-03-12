#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   estimators.py    
@Contact :   huanghoward@foxmail.com
@Modify Time :    2021/9/8 14:21  
------------      
"""
from multiprocessing import Pool

import numpy as np

from bnsl.base import Estimator
from bnsl.bionics import Genetic
from bnsl.dp import generate_order_graph, generate_parent_graph, order2dag
from bnsl.expert import Expert
from bnsl.heuristic import HillClimb, SimulatedAnnealing
from bnsl.pc import *
from bnsl.score import BIC_score, MDL_score, Knowledge_fused_score
from bnsl.k2 import order_to_dag


class DP(Estimator):
    """ Dynamic program estimator class
    reference: 《Learning Optimal Bayesian Networks: A Shortest Path Perspective》
    :param: data, np.array or pd.Dataframe
    """

    def __init__(self, data):
        super(DP, self).__init__()
        self.load_data(data)

    def run(self, score_method=MDL_score):
        """
        run the dynamic program estimator, an exact algorithm. MDL score is used as the score criteria, it return the
        dag with minimum score.
        :param score_method: MDL score
        :return: the dag with minimum score
        """
        pg = generate_parent_graph(self.data, score_method)
        og = generate_order_graph(self.data, pg)
        self.result = order2dag(og, self.data)
        return self.result


class HC(Estimator):
    """
    Greedy hill climb estimator
    """

    def __init__(self, data):
        super(HC, self).__init__()
        self.load_data(data)

    def run(self, score_method=BIC_score, direction='up', initial_dag=None, max_iter=10000, restart=1, explore_num=5,**kwargs):
        """
        run the HC estimator.
        :param explore_num:
        :param score_method: score method, usually select BIC score or BDeu score
        :param direction:  try to find the maximum of minimum score
        :param initial_dag: the initial dag
        :param max_iter: the number of maximum iteration
        :param restart: the number of restart times, every restart will random initialize a start DAG
        :return: an approximate maximum or minimum scored DAG
        """
        s = score_method(self.data, **kwargs)
        hc = HillClimb(self.data, s, initial_dag=initial_dag, max_iter=max_iter,
                       restart=restart, explore_num=explore_num)
        self.result = hc.climb(direction)
        return self.result

    def run_parallel(self, worker=4, **kwargs):
        """
        :return:
        """
        kwargs["instance"] = self
        arguments = [kwargs for i in range(worker)]
        with Pool(processes=worker) as pool:
            result = pool.map(_process, arguments)
        i = np.argmax([dag.calculated_score for dag in result])
        self.result = result[i]
        return self.result


def _process(arguments):
    result = arguments["instance"].run(**arguments)
    return result








class SA(Estimator):
    """
    
    """

    def __init__(self, data, score_method=BIC_score, **kwargs):
        super(SA, self).__init__()
        self.load_data(data)
        self.show_est()
        self.score_method = score_method(data)

    def run(self):
        sa = SimulatedAnnealing(self.data, self.score_method)
        self.result = sa.run()
        return self.result


class PC(Estimator):
    def __init__(self, data):
        """

        :param data:
        """
        super(PC, self).__init__()
        self.load_data(data)
        self.show_est()

    def run(self):
        skl, sep_set = estimate_skeleton(self.data)
        cpdag = estimate_cpdag(skl, sep_set)
        cpdag = nx.relabel.relabel_nodes(cpdag, dict(zip(range(len(data.columns)), data.columns)))
        self.result = cpdag
        return self.result


class GA(Estimator):
    """
    Genetic algorithm estimator class
    """

    def __init__(self, data):
        super(GA, self).__init__()
        self.load_data(data)
        self.history = None

    def run(self, num_parent=5, score_method=BIC_score, pop=40, max_iter=150, c1=0.5, c2=0.5,
            w=0.05, patience=20, return_history=False):
        """
        run the genetic algorithm estimator
        :param patience:
        :param num_parent:
        :param return_history:
        :param score_method: score criteria
        :param pop: number of population
        :param max_iter: maximum iteration number
        :param c1: [0,1] the probability of crossover with personal historical best genome
        :param c2: [0,1] the probability of crossover with global historical best genome
        :param w: the probability of mutation
        :return: the dag with maximum score
        """
        ga = Genetic(self.data, num_parent=num_parent, score_method=score_method, pop=pop, max_iter=max_iter, c1=c1,
                     c2=c2,
                     w=w, patience=patience)
        self.result = ga.run()
        self.history = ga.history
        if return_history:
            return self.result, self.history
        else:
            return self.result


class KBNL(Estimator):
    """
    KBNL estimator, observed data, expert data and expert confidence are needed to initialize the estimator.
    """

    def __init__(self, data, expert_data: list, expert_confidence: list, ):
        super(KBNL, self).__init__()
        self.load_data(data)
        if isinstance(expert_data[0], pd.DataFrame):
            self.expert = Expert(expert_data, expert_confidence)
        if isinstance(expert_data[0], str):
            self.expert = Expert.read(expert_data, confidence=expert_confidence)

    def run(self, initial_dag=None, max_iter=10000, restart=5, explore_num=5,**kwargs):
        """
        run the KBNL estimator.
        :param initial_dag: the initial dag
        :param max_iter: the number of maximum iteration
        :param restart: the number of restart times, every restart will random initialize a start DAG
        :param explore_num:
        :return: an maximum knowledge fused scored DAG
        """
        s = Knowledge_fused_score(self.data, self.expert)
        hc = HillClimb(self.data, s, initial_dag=initial_dag, max_iter=max_iter,
                       restart=restart, explore_num=explore_num, **kwargs)
        self.result = hc.climb()
        return self.result

    def run_parallel(self, worker=4, **kwargs):
        """
        :return:
        """
        kwargs["instance"] = self
        arguments = [kwargs for i in range(worker)]
        with Pool(processes=worker) as pool:
            result = pool.map(_process, arguments)
        print([dag.calculated_score for dag in result])
        i = np.argmax([dag.calculated_score for dag in result])
        self.result = result[i]
        return self.result

class K2(Estimator):
    def __init__(self, data: pd.DataFrame, score_method=BIC_score):
        super(K2).__init__()
        self.score_method = score_method(data)
        self.order = list(data.columns)

    def run(self):
        self.result = order_to_dag(self.order, 3, self.score_method)
        return self.result