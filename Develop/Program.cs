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
            var visa = new AgilentVisaCommunicator("GPIB0::18::INSTR");
            visa.SetTimeout(600);
            //SweepMeasurement(visa, 500e-3, .5e-3, 1e-3, 1, 3, 1e-6);
            ContactTest(visa, 100e-3, 20);
        }
    }
}
