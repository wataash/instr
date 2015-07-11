using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Instr;

namespace Develop
{
    class Program
    {
        static void Main(string[] args)
        {
            var visa = new AgilentVisaCommunicator("GPIB0::18::INSTR");
            visa.Query("*IDN?");
            visa.Write("*IDN?");
            visa.Read();
        }
    }
}
