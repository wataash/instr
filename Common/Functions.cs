using System;
using System.Collections.Generic;
using System.Linq;

enum Unit
{
    SMU1, SMU2, SMU3, SMU4, VSU1, VSU2, VMU1, VMU2
}

namespace Instr
{
    public static class Functions
    {
        /// <summary>
        /// Write2DimDouble(
        ///     new[] { new[] { 1.0, 2, }, new[] { 3.0, 4 } });
        /// returns "1,2\n3,4" // TODO: "1,2,\n3,4\n"? check
        /// </summary>
        /// <param name="data"></param>
        public static string TwoDimDouble2String(double[][] data)
        {
            string joined = "";
            foreach (double[] item in data)
            {
                joined += String.Join(",", item) + "\n";
            }
            return joined;
        }

        /// <summary>
        /// CommaStringToDoubleArray("1,2,3e3") --> {1.0, 2.0, 3000.0}
        /// </summary>
        /// <param name="s"></param>
        /// <returns></returns>
        public static double[] CommaStringToDoubleArray(string s)
        {
            return Array.ConvertAll(s.Split(','), Double.Parse);
        }

        /// <summary>
        /// </summary>
        /// <param name="start"></param>
        /// <param name="delta"></param>
        /// <param name="end"></param>
        /// <returns></returns>
        /// <example>
        /// AlternativeRange(1.00, 0.11, 1.55)
        /// returns {1.00, -1.00, 1.11, -1.11, 1.22, -1.22}
        /// </example>
        public static double[] AlternativeRange(double start, double delta, double end)
        {
            // TODO: smart way using LINQ?
            var res = new List<double>();
            double append = start;
            while (append <= end)
            {
                res.Add(append);
                res.Add(-append);
                append += delta;
            }
            return res.ToArray();
        }

        /// <summary>
        /// Zip_(new[] {1, 2, 3 }, new[] {4, 5, 6});
        /// returns {{1,4},{2,5},{3,6}}.
        /// Zip_(new[] {1,2}, new[] {3}); 
        /// returns {{1,3}}.
        /// Zip_(new[] {1,2}, new int[] {}); 
        /// returns {{}}.
        /// Zip_(new[] {"a"}, new[] {"b"});
        /// returns {{"a","b"}}.
        /// Zip_(new[] {"a,b,c"}, new[] {"d"}); 
        /// returns {{"a,b,c","d"}}.
        /// </summary>
        /// <typeparam name="T"></typeparam>
        /// <param name="arr1"></param>
        /// <param name="arr2"></param>
        /// <returns></returns>
        public static T[][] Zip_<T>(T[] arr1, T[] arr2)
        {
            IEnumerable<T[]> z = arr1.Zip(arr2, (a, b) => new[] { a, b });
            return z.ToArray();
        }

        /// <summary>
        /// Zip_(new[] {1, 2, 3}, new[] {4, 5, 6}, new[] {7, 8, 9}); 
        /// returns {{1,4,7},{2,5,8},{3,6,9}}.
        /// </summary>
        /// <typeparam name="T"></typeparam>
        /// <param name="arr1"></param>
        /// <param name="arr2"></param>
        /// <param name="arr3"></param>
        /// <returns></returns>
        public static T[][] Zip_<T>(T[] arr1, T[] arr2, T[] arr3)
        {
            IEnumerable<T[]> z = arr1.Zip(arr2, (a, b) => new[] { a, b }).
                Zip(arr3, (a, b) => new T[] { a[0], a[1], b });
            return z.ToArray();
        }

        /// <summary>
        /// double[][] o;
        /// ZipDetectInf(new[] { 1, 1e20, 3 }, new[] { 1.1, 3.3, 800 }, out o);
        /// returns true (1e20 > 1e10), o = new[][] {{1.0, 1.1}, {3.0, 800.0}}
        /// </summary>
        /// <param name="in1"></param>
        /// <param name="in2"></param>
        /// <param name="o"></param>
        /// <param name="inf">Threshold.</param>
        /// <returns></returns>
        public static bool ZipDetectInf(double[] in1, double[] in2, out double[][] o, double inf = 1e10)
        {
            // TODO: use SearchInf()?
            bool detectInfinity = false;
            IEnumerable<double[]> zipped = in1.Zip(in2, (a, b) => new[] { a, b });
            var zipInfRemoved = new List<double[]>();
            foreach (double[] pair in zipped)
            {
                if (pair[0] > inf || pair[1] > inf)
                    detectInfinity = true;
                else
                    zipInfRemoved.Add(pair);
            }
            o = zipInfRemoved.ToArray();
            return detectInfinity;
        }

        /// <summary>
        /// SearchInf(new[] {1.0, 1e11, -1e11, 1e11}, 1e10);
        /// returns {1, 3}.
        /// SearchInf(new double[] {}, 1e10);
        /// returns { }.
        /// SearchInf(new[] {0.0}, 1e10);
        /// returns{ }.
        /// </summary>
        /// <param name="arr"></param>
        /// <param name="inf">Threshold.</param>
        /// <returns></returns>
        public static int[] SearchInf(double[] arr, double inf = 1e10)
        {
            var infIndices = new List<int>();
            for (int i = 0; i < arr.Length; i++)
                if (arr[i] > inf) infIndices.Add(i);
            return infIndices.ToArray();
        }

    }
}
