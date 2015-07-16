using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Net.Mime;
using System.Text;
using System.Threading.Tasks;
using static Instr.Functions;

namespace Instr.Develop
{
    internal class Program
    {
        private static void Main(string[] args)
        {
            string writeStrToFile, fileName;
            var s = new SussPA300("GPIB0::7::INSTR") { TimeoutSecond = 5 };
            var a = new Agilent4156C("GPIB0::18::INSTR", false) { TimeoutSecond = 600 };

            // initial state: calibrated, set home to subs LD, set z, align
            double D = 1300; // Move Delta [um]
            double xOffset = 791; // [um]
            double yOffset = 794;
            int[][] XYs = { new[] { 2, 2 }, new[] { 2, 1 }, new[] { 3, 1 } };

            double xH, yH; // xy [um] from home position
            double[][] ti; // time, current
            string t0;
            foreach (int[] XY in XYs)
            {
                xH = -((XY[0] - 1) * D) + xOffset;
                yH = -((XY[1] - 1) * D) + yOffset;
                s.MoveChuckHCont(xH, yH, 0);

                // TODO: RDB xH yH

                t0 = GetTime2();
                ti = a.ContactTest(1, 3, points: 100);
                fileName = $"ContactTest_{t0}_E0326-2-1_X{XY[0]}_Y{XY[1]}_D5.54.csv";
                writeStrToFile = String.Join(",", ti[0]) + "\n" + String.Join(",", ti[1]) + "\n";
                Save(fileName, writeStrToFile);

                s.Align();
                s.Contact();

                t0 = GetTime2();
                ti = a.ContactTest(1, 3, points: 100);
                fileName = $"ContactTest_{t0}_E0326-2-1_X{XY[0]}_Y{XY[1]}_D5.54.csv";
                writeStrToFile = String.Join(",", ti[0]) + "\n" + String.Join(",", ti[1]) + "\n";
                Save(fileName, writeStrToFile);

                s.Align();
                s.Contact();

                t0 = GetTime2();
                ti = a.ContactTest(1, 3, points: 100);
                fileName = $"ContactTest_{t0}_E0326-2-1_X{XY[0]}_Y{XY[1]}_D5.54.csv";
                writeStrToFile = String.Join(",", ti[0]) + "\n" + String.Join(",", ti[1]) + "\n";
                Save(fileName, writeStrToFile);

                s.Align();
            }

            //// ContactTest
            //double[][] tiPairs = a.ContactTest(1, 3);
            //writeStrToFile = "t,I\n" + TwoDimDouble2String(tiPairs);
            //Save($"ContactTest_{GetTime()}.txt", writeStrToFile);
            //Save("last.txt", writeStrToFile);

            // DoubleSweepFromZero
            //bool aborted = false;
            //List<double[]> ivPairsAccum = new List<double[]>();
            //foreach (double v in AlternativeRange(100e-3, 100e-3, 200e-3)) // 100mV step
            //{
            //    // TODO: double acuumulate[][], save it
            //    // TODO: header
            //    // ivPairs: { {0,1E-13}, {0.001,1.7E-13}, ... }
            //    //double[][] ivPairs = a.DoubleSweepFromZero(1, 3, v, 0.1e-3, out aborted);
            //    string t0 = GetTime();
            //    int R = 1, C = 1;
            //    string mesa = "D56.3";
            //    int status = 255;
            //    List<double[]> ivPairs = DummyReturnsDoublePairs().ToList();
            //    int points = ivPairs.Count;

            //    writeStrToFile = $"t0={t0},sample=E0326-2-1,R={R},C={C},mesa={mesa},status={status},";
            //    writeStrToFile += "V,I\n" + TwoDimDouble2String(ivPairs.ToArray());
            //    Save($"DoubleSweepFromZero_{t0}.txt", writeStrToFile);
            //    Save("last.txt", writeStrToFile);

            //    ivPairsAccum = ivPairsAccum.Concat(ivPairs).ToList();
            //    if (aborted) break; // Finish if "stop button" on 4156C pressed.
            //}
            // Rerational DB
            // I-V: V, I, t0, t
            // params:  t0, sample, X, Y, mesa, status, measPoints, comp, instr, iter, originalFilename
            // status: 0 valid, 1 invalid, 2 BD, 3: mecha BD, 4: process failed, 5: unstable I-V, 255: unconfirmed
            // mesa: D5.54, D16.7, D56.3, D169
        }

        private static void Save(string fileName, string text)
        {
            string filePath = Environment.ExpandEnvironmentVariables("%appdata%") +
                              $@"\Instr\Agilent4156C\" + fileName;
            (new FileInfo(filePath)).Directory.Create();
            File.WriteAllText(filePath, text);
        }

        private static double[][] DummyReturns2DimDouble()
        {
            return new[] { new[] { 0e-3, 1e-3, 2e-3, 3e-3 }, new[] { 1e-6, 1.2e-6, 1.5e-6, 2e-6 } };
        }

        private static double[][] DummyReturnsDoublePairs()
        {
            return new[]
            {
                new[] {0e-3, 1e-6},
                new[] {1e-3, 1.2e-6},
                new[] {2e-3, 1.5e-6},
                new[] {3e-3, 2e-6}
            };
        }

    }
}
