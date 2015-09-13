#ifndef CONDITIONED_SFS_H
#define CONDITIONED_SFS_H

#include <cassert>
#include <cfenv>
#include <map>
#include <thread>
#include <random>
#include <unsupported/Eigen/MPRealSupport>
#include <mpreal.h>
#include <gmpxx.h>

#include "common.h"
#include "piecewise_exponential_rate_function.h"
#include "moran_eigensystem.h"
#include "ThreadPool.h"
#include "mpq_support.h"

typedef struct 
{
    MatrixXq coeffs;
    mp_prec_t prec;
} below_coeff;

typedef struct { MatrixXq X0, X2, M0, M1; mp_prec_t prec; } MatrixCache;

class ConditionedSFSBase
{
    protected:
    static std::map<int, below_coeff> below_coeffs_memo;
    static MatrixCache& cached_matrices(int n);
    static std::map<int, MatrixCache> matrix_cache;
};

template <typename T>
class ConditionedSFS : public ConditionedSFSBase
{
    public:
    ConditionedSFS(int);
    std::vector<Matrix<T> > compute(const PiecewiseExponentialRateFunction<T> &, double);

    // private:
    // Methods
    void construct_ad_vars();
    Matrix<T> above0(const Matrix<T>&);
    Matrix<T> above2(const Matrix<T>&);
    Matrix<T> below0(const Matrix<mpreal_wrapper<T> >&);
    Matrix<T> below1(const Matrix<mpreal_wrapper<T> >&);
    template <typename Derived>
    Matrix<T> parallel_cwiseProduct_colSum(const MatrixXq &a, const Eigen::MatrixBase<Derived> &b);
    template <typename Derived>
    Matrix<mpreal_wrapper<T> > parallel_matrix_product(const Eigen::MatrixBase<Derived> &, const MatrixXq &);
    // Vector<T> compute_etnk_below(const Vector<T>&);
    // Vector<T> compute_etnk_below(const std::vector<mpreal_wrapper<T> >&);
    Matrix<T> compute_etnk_below_mat(const Matrix<mpreal_wrapper<T> >&);
    std::vector<Matrix<T> > compute_below(const PiecewiseExponentialRateFunction<T> &);
    std::vector<Matrix<T> > compute_above(const PiecewiseExponentialRateFunction<T> &);

    // Variables
    const int n;
    const MoranEigensystem mei;
    const MatrixCache mcache;
    // ThreadPool tp;
};
/*

class CSFSManager
{
    public:
    CSFSManager(int n, int num_threads) : csfs_d(n, num_threads), csfs_ad(n, num_threads) {}

    template <typename T>
    std::vector<Matrix<T> > compute(const PiecewiseExponentialRateFunction<T> &eta, double theta)
    {
        return csfs
        std::vector<Matrix<T> > ret2;
        return ret2;
        // ConditionedSFS<T> c(n);
        /*
        Matrix<T> below = c0.compute_below();
        Matrix<T> above = c0.compute_above();
        std::future<std::vector<Matrix<T> > > below_res(tp_.enqueue(
            [&cc0, eta] { return cc0.compute_below(eta); }));
        for (int h = 1; h < hidden_states.size(); ++h)
        {
            double tau1 = hidden_states[h - 1];
            double tau2 = hidden_states[h];
            std::vector<std::thread> t;
            T t1 = (*eta.getR())(tau1);
            T t2;
            if (std::isinf(tau2))
                t2 = INFINITY;
            else
                t2 = (*eta.getR())(tau2);
            std::vector<std::future<void>> results;
            for (ConditionedSFS<T> &c : csfss)
                results.emplace_back(tp_.enqueue([&c, eta, num_samples, t1, t2] { c.compute(eta, num_samples, t1, t2); }));
            for (auto &res : results) 
                res.wait();
            Eigen::Matrix<T, 3, Eigen::Dynamic> ret = average_csfs();
            ret2.push_back(ret);
        }
        std::vector<Matrix<T> > below = below_res.get();
        for (size_t h = 0; h < hidden_states.size() - 1; ++h)
        {
            ret2[h] += below[h];
            T tauh = ret2[h].sum();
            ret2[h] *= -expm1(-theta_ * tauh) / tauh;
            ret2[h](0, 0) = exp(-theta_ * tauh);
            // ret *= theta;
            // ret(0, 0) = 1. - ret.sum();
        }
        return ret2;
    }
    ConditionedSFS<T> csfs;
    double theta_;
    std::mt19937 gen;
};

*/

#endif
