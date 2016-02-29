'Fit SMC++ to data using the EM algorithm'

from __future__ import division, print_function
import numpy as np
import scipy.optimize
import pprint
import multiprocessing
import sys
import itertools
import sys
import time
import logging
logger = logging.getLogger(__name__)
import os
import traceback

# Package imports
from .. import _smcpp, util, estimation_tools
from ..model import SMCModel
from ..population import Population
from ..inference_service import DumbInferenceService as InferenceService
from ..optimizer import PopulationOptimizer, TwoPopulationOptimizer
from ..util import init_logging

np.set_printoptions(linewidth=120, suppress=True)

def init_parser(parser):
    '''Configure parser and parse args.'''
    # FIXME: argument groups not supported in subparsers
    pop_params = parser # parser.add_argument_group('population parameters')
    model = parser # parser.add_argument_group('model')
    hmm = parser # parser.add_argument_group('HMM and fitting parameters')
    model.add_argument('--pieces', type=str, help="span of model pieces", default="32*1")
    model.add_argument('--t1', type=float, help="end-point of first piece, in generations", default=400.)
    model.add_argument('--tK', type=float, help="end-point of last piece, in generations", default=40000.)
    model.add_argument('--exponential-pieces', type=int, action="append", default=[], help="pieces which have exponential growth")
    hmm.add_argument('--thinning', help="emit full SFS every <k>th site", default=10000, type=int, metavar="k")
    hmm.add_argument('--no-pretrain', help="do not pretrain model", action="store_true", default=False)
    hmm.add_argument('--M', type=int, help="number of hidden states", default=32)
    hmm.add_argument('--em-iterations', type=int, help="number of EM steps to perform", default=20)
    hmm.add_argument('--regularization-penalty', type=float, help="regularization penalty", default=.01)
    hmm.add_argument('--regularizer', choices=["abs", "quadratic"], default="quadratic", help="type of regularization to apply")
    hmm.add_argument('--lbfgs-factor', type=float, help="stopping criterion for optimizer", default=1e9)
    hmm.add_argument('--Nmin', type=float, help="Lower bound on effective population size", default=1000)
    hmm.add_argument('--Nmax', type=float, help="Upper bound on effective population size", default=400000)
    hmm.add_argument('--span-cutoff', help="treat spans > as missing", default=50000, type=int)
    hmm.add_argument('--length-cutoff', help="omit sequences < cutoff", default=1000000, type=int)
    parser.add_argument("-p", "--second-population", nargs="+", widget="MultiFileChooser", 
            help="Estimate divergence time using data set(s) from a second subpopulation")
    parser.add_argument("-o", "--outdir", help="output directory", default="/tmp", widget="DirChooser")
    parser.add_argument('-v', '--verbose', action='store_true', help="generate tremendous amounts of output")
    pop_params.add_argument('--N0', default=1e4, type=float, help="reference effective (diploid) population size to scale output.")
    pop_params.add_argument('mu', type=float, help="per-generation mutation rate")
    pop_params.add_argument('r', type=float, help="per-generation recombination rate")
    parser.add_argument('data', nargs="+", help="data file(s) in SMC++ format", widget="MultiFileChooser")

def main(args):
    'Main control loop for EM algorithm'
    ## Create output directory and dump all values for use later
    try:
        os.makedirs(args.outdir)
    except OSError:
        pass # directory exists

    ## Initialize the logger
    init_logging(args.outdir, args.verbose, ".debug.txt")
    
    ## Begin main script
    ## Step 1: load data and clean up a bit
    datasets_files = [args.data]
    if args.second_population:
        logger.info("Split estimation mode selected")
        datasets_files.append(args.second_population)
    
    ## Build time intervals
    t1 = args.t1 / (2 * args.N0)
    tK = args.tK / (2 * args.N0)
    pieces = estimation_tools.extract_pieces(args.pieces)
    time_points = estimation_tools.construct_time_points(t1, tK, pieces)
    logger.debug("time points in coalescent scaling:\n%s", str(time_points))
    K = len(time_points)

    ## Construct bounds
    Nmin = args.Nmin / (2 * args.N0)
    Nmax = args.Nmax / (2 * args.N0)
    bounds = np.array([[Nmin, Nmax]] * K + 
            [[1.01 * Nmin, 0.99 * Nmax]] * K).reshape([2, K, 2])


    ## Construct populations
    populations = [
            (dsf, time_points, args.exponential_pieces, args.N0,
                2 * args.mu * args.N0, 2 * args.r * args.N0, args.M, bounds, args)
            for dsf in datasets_files
            ]

    ## Initialize the "inference server"
    iserv = InferenceService(populations)

    npop = len(populations)
    if npop == 1:
        opt_klass = PopulationOptimizer
    elif npop == 2:
        opt_klass = TwoPopulationOptimizer
    else:
        raise RuntimeError("> 2 populations not currently supported")
    opt = opt_klass(iserv, bounds, args)

    # Run the optimizer
    opt.run(args.em_iterations)

    iserv.close()