using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Agilent4156C
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            var RM = new Ivi.Visa.Interop.ResourceManager();
            var DMM = new Ivi.Visa.Interop.FormattedIO488();
            DMM.IO = (Ivi.Visa.Interop.IMessage)RM.Open("GPIB0::18::INSTR");
            DMM.WriteString("*IDN?");
            textBox1.Text = DMM.ReadString();
            DMM.IO.Close();
            System.Runtime.InteropServices.Marshal.ReleaseComObject(DMM);
            System.Runtime.InteropServices.Marshal.ReleaseComObject(RM);
        }
    }
}
