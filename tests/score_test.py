#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   score_test.py    
@Contact :   huanghoward@foxmail.com
@Modify Time :    2022/1/5 20:53  
------------      
"""
import unittest

import pandas as pd

from bnsl.expert import Expert
from bnsl.score import Knowledge_fused_score, BIC_score, MDL_score


class Test_Expert(unittest.TestCase):

    def test_mdl(self):
        data = pd.read_csv(r"test_data/Asia.csv")
        mdl = MDL_score(data)
        ls0 = mdl.local_score('tub', tuple())
        ls1 = mdl.local_score('tub', tuple(['asia']))
        print(ls0, ls1)
