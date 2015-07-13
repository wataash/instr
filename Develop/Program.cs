using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Instr;
using static Instr.Functions;

namespace Develop
{
    class Program
    {
        static void Main(string[] args)
        {
            var a = new Agilent4156C("GPIB0::18::INSTR", false);
            a.TimeoutSecond = 600;
            double[][] dat = a.ContactTest(1, 3);

            bool aborted;
            foreach (double v in AlternativeRange(0.1, 0.1, 0.5)) // 100mV step
            {
                a.DoubleSweepFromZero(1, 3, v, 0.1e-3, 10e-3, 1, out aborted);
                if (aborted) break; // Finish if "stop button" on 4156C pressed.
            }

            string writeStr = "\nt,I\n";
            writeStr += TwoDimDouble2String(dat);
            string filePath = Environment.ExpandEnvironmentVariables("%appdata%") +
                $@"\Instr\Agilent4156C{GetTime()}.txt";
            string lastFilePath = Environment.ExpandEnvironmentVariables("%appdata%") +
                @"\Instr\Agilent4156C\last.txt";
            (new FileInfo(filePath)).Directory.Create();
            File.WriteAllText(filePath, writeStr);
            File.WriteAllText(lastFilePath, writeStr);
        }
    }
}
