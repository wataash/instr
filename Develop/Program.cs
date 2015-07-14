using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static Instr.Functions;

namespace Instr.Develop
{
    class Program
    {
        static void Main(string[] args)
        {
            var s = new SussPA300("GPIB0::7::INSTR") { TimeoutSecond = 5 };

            var a = new Agilent4156C("GPIB0::18::INSTR", false) { TimeoutSecond = 600 };

            string writeStr;

            //// ContactTest
            //double[][] tiPairs = a.ContactTest(1, 3);
            //writeStr = "t,I\n" + TwoDimDouble2String(dat);
            //Save($"ContactTest_{GetTime()}.txt", writeStr);
            //Save("last.txt", writeStr);

            // DoubleSweepFromZero
            bool aborted = false;
            foreach (double v in AlternativeRange(100e-3, 100e-3, 200e-3)) // 100mV step
            {
                // TODO: double acuumulate[][], save it
                // TODO: header
                // dat: { {0,1E-13}, {0.001,1.7E-13}, ... }
                double[][] ivPairs = a.DoubleSweepFromZero(1, 3, v, 0.1e-3, out aborted);
                // Plot(
                writeStr = "V,I\n" + TwoDimDouble2String(ivPairs);
                Save($"DoubleSweepFromZero_{GetTime()}.txt", writeStr);
                Save("last.txt", writeStr);
                if (aborted) break; // Finish if "stop button" on 4156C pressed.
            }
            // Rerational DB
            // I-V: V, I, t0, t
            // params:  t0, sample, R, C, mesa, status, measPoints, comp, instr, iter, originalFilename
            //    add x y, del 
            // status: 0 valid, 1 invalid, 2 BD, 3: mecha BD, 4: process failed, 5: unstable I-V, 255: unconfirmed
            // mesa: D5.54, D16.7, D56.3, D169
        }

        static void Save(string fileName, string text)
        {
            string filePath = Environment.ExpandEnvironmentVariables("%appdata%") +
                $@"\Instr\Agilent4156C\" + fileName;
            (new FileInfo(filePath)).Directory.Create();
            File.WriteAllText(filePath, text);
        }

        static double[][] DummyReturns2DimDouble()
        {
            return new[] { new[] { 0e-3, 1e-3, 2e-3, 3e-3 }, new[] { 1e-6, 1.2e-6, 1.5e-6, 2e-6 } };
        }

    }
}
