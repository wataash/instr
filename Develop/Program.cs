#define A

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Instr;
using static Instr.Agilent4156C;

namespace Develop
{
    class Program
    {
        static void Main(string[] args)
        {
            var a = new Agilent4156C("GPIB0::18::INSTR", false);
            a.TimeoutSecond = 600;
            a.ContactTest(100e-3, 20);
            //a.SweepMeasurement(500e-3, .5e-3, 1e-3, 1, 3, 1e-6);
        }
    }
}
