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
        /// </summary>
        /// <param name="data"></param>
        /// <example>
        /// <code>
        /// Write2DimDouble(
        ///     new[] { new[] { 1.0, 2, }, new[] { 3.0, 4 } });
        /// returns "1,2\n3,4"
        /// </code>
        /// </example>
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
        /// </summary>
        /// <returns>Example: "2015-07-06_20-13-08"</returns>
        /// <remarks>Verified only in Japanese locale.</remarks>
        public static string GetTime()
        {
            string t = DateTime.Now.ToString();
            // 2015/07/06 20:13:08 --> 2015-07-06_20-13-08
            return t.Replace(":", "-").Replace("/", "-").Replace(" ", "_");
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
        /// Grater than 1e10: Infinite.
        /// </summary>
        /// <param name="in1"></param>
        /// <param name="in2"></param>
        /// <param name="o"></param>
        /// <returns></returns>
        /// <example>
        /// double[][] o;
        /// ZipDetectInf(new[] { 1, 1e20, 3 }, new[] { 1.1, 3.3, 800 }, out o);
        /// returns true (1e20 > 1e10), o = new[][] {{1.0, 1.1}, {3.0, 800.0}}
        /// </example>
        public static bool ZipDetectInf(double[] in1, double[] in2, out double[][] o)
        {
            bool detectInfinity = false;
            IEnumerable<double[]> zipped = in1.Zip(in2, (a, b) => new[] { a, b });
            var zipInfRemoved = new List<double[]>();
            foreach (double[] pair in zipped)
            {
                if (pair[0] > 1e10 || pair[1] > 1e10)
                    detectInfinity = true;
                else
                    zipInfRemoved.Add(pair);
            }
            o = zipInfRemoved.ToArray();
            return detectInfinity;
        }
    }
}
