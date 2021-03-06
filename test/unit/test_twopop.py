import numpy as np
import sys
import logging
import ad
import pytest

import fixtures
import smcpp._smcpp, smcpp.model, smcpp.jcsfs


@pytest.fixture
def hs():
    return [0, 0.002, 0.0024992427075529156, 0.0031231070556282147,
            0.0039027012668429368, 0.0048768988404573679, 0.0060942769312431738,
            0.0076155385891087321, 0.0095165396414589112, 0.011892071150027212,
            0.014860586049702963, 0.018570105657341358, 0.023205600571298769,
            0.028998214001102113, 0.036236787437156658, 0.045282263373729439,
            0.0565856832591419, 0.070710678118654752, 0.088361573317084705,
            0.11041850887031313, 0.1379813265364985, 0.15879323234898887,
            0.22690003122622915, 0.28675095012241164, 0.35039604900931776,
            0.4174620285802807, 0.48093344839252727, 0.54048403452772453,
            0.58902987679112695, 0.63973400753929655, 0.6661845719884536,
            0.68097444812291441, 0.69652310395210704, 0.71291262669986732,
            0.73023918985303526, 0.74861647270557707, 0.76818018497781393,
            0.7890941548490632, 0.81155867710242946, 0.8429182938518559,
            0.88146343535942318, 0.92368486081866963, 0.97035848127888702,
            1.0225351498208244, 1.1293598575982273, 1.2553186915845398,
            1.468142830257521, 1.7982719448467761, 2.3740247153419043,
            3.2719144602927757, 4.8068671176749671, np.inf]

@pytest.fixture
def s():
    return [0.002, 0.00049924270755291556, 0.00062386434807529907,
            0.00077959421121472213, 0.00097419757361443156, 0.0012173780907858058,
            0.0015212616578655584, 0.0019010010523501783, 0.0023755315085683005,
            0.0029685148996757508, 0.0037095196076383959, 0.0046354949139574102,
            0.0057926134298033442, 0.0072385734360545448, 0.0090454759365727819,
            0.011303419885412461, 0.014124994859512852, 0.017650895198429953,
            0.022056935553228421, 0.027562817666185374, 0.034443085525912243,
            0.043040815163128798, 0.0537847217117913, 0.067210536757978667,
            0.083987721931547688, 0.10495285078070138, 0.13115132347527858,
            0.16388949439075173, 0.20479981185031038, 0.25592221813754867,
            0.31980586869051764, 0.39963624257870101, 0.49939398246933342]

def test_inference_together(hs, s):
    K = 10
    model1 = smcpp.model.SMCModel(s, np.logspace(
        np.log10(.01), np.log10(3.), K))
    model2 = smcpp.model.SMCModel(s, np.logspace(
        np.log10(.01), np.log10(3.), K))
    n = 10
    fakeobs = [[1, -1, 0, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0, 0], [10, 0, 0, 0, 0, 0, 0],
               [10, -1, 0, 0, 0, 0, 0], [200000, 0, 0, n - 2, 0, 0, n - 1],
               [1, 2, n - 4, n - 2, 0, n - 3, n - 1]]
    # fakeobs *= 20
    im = smcpp._smcpp.PyTwoPopInferenceManager(
        n - 2, n - 1, 2, 0, np.array(
            [fakeobs] * 2, dtype=np.int32), hs)
    model1[:] = [ad.adnumber(x, i) for i, x in enumerate([
        0.002676322760403453, -0.010519987448975402,
        0.006727140517177145, 0.0031333684894676865,
        -0.02302979056648467, 0.0026368097606793172,
        0.001992156262601299, 0.004958301100037235,
        0.003199704865436452, 0.0050129872575249744
        ])]
    model2[:] = model1[:].astype('float')
    split = 0.5
    model = smcpp.model.SMCTwoPopulationModel(model1, model2, split)
    im.model = model
    im.theta = 0.0025000000000000001
    im.rho = 0.0031206103977654887
    im.E_step()
    q0 = im.Q()
    for k in range(K):
        coord = (0, k)
        dq = q0.d(model[coord])
        model[coord] += 1e-8
        im.model = model
        q1 = im.Q()
        a = float(q1 - q0) * 1e8
        print(k, a, dq)
        model[coord] -= 1e-8

def test_inference_apart(hs, s):
    K = 10
    model1 = smcpp.model.SMCModel(s, np.logspace(
        np.log10(.01), np.log10(3.), K))
    model2 = smcpp.model.SMCModel(s, np.logspace(
        np.log10(.01), np.log10(3.), K))
    n = 10
    fakeobs = [[1, -1, 0, 0, -1, 0, 0], [1, 1, 0, 0, 1, 0, 0], [10, 0, 0, 0, 0, 0, 0],
               [10, -1, 0, 0, 1, 0, 0], [200000, 1, 0, n - 2, 0, 0, n - 1],
               [1, 0, n - 4, n - 2, -1, n - 3, n - 1],
               [1, 0, n - 4, n - 2, 1, n - 3, n - 1],
               [1, 1, n - 4, n - 2, 1, n - 3, n - 1]]
    # fakeobs *= 20
    im = smcpp._smcpp.PyTwoPopInferenceManager(
        n - 2, n - 1, 1, 1, np.array(
            [fakeobs] * 2, dtype=np.int32), hs)
    model1[:] = [ad.adnumber(x, i) for i, x in enumerate([
        0.002676322760403453, -0.010519987448975402,
        0.006727140517177145, 0.0031333684894676865,
        -0.02302979056648467, 0.0026368097606793172,
        0.001992156262601299, 0.004958301100037235,
        0.003199704865436452, 0.0050129872575249744
        ])]
    model2[:] = model1[:].astype('float')
    split = 0.5
    model = smcpp.model.SMCTwoPopulationModel(model1, model2, split)
    im.model = model
    im.theta = 0.0025000000000000001
    im.rho = 0.0031206103977654887
    im.E_step()
    e = im.emission_probs
    q0 = im.Q(1)
    for k in range(K):
        coord = (0, k)
        dq = q0.d(model[coord])
        model[coord] += 1e-8
        im.model = model
        q1 = im.Q(1)
        a = float(q1 - q0) * 1e8
        print(k, a, dq)
        model[coord] -= 1e-8
