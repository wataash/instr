#define IVI
#undef NI

using System;

namespace Instr
{
    public interface IVisaCommunicator
    {
        string Read();
        void Write(string writeText);
        string Query(string writeText);
        [Obsolete]
        void SetTimeout(double second);
        int TimeoutSecond { get; set; }
    }

#if IVI
    // for Agilent 82357A
    // needs "VISA COM 5.5 Type Library"
    public class VisaCommunicator : IVisaCommunicator
    {
        private int timeoutSecond;
        private Ivi.Visa.Interop.ResourceManager rm;
        private Ivi.Visa.Interop.FormattedIO488 io;

        public VisaCommunicator(string visaResource)
        {
            rm = new Ivi.Visa.Interop.ResourceManager();
            io = new Ivi.Visa.Interop.FormattedIO488();
            io.IO = (Ivi.Visa.Interop.IMessage)rm.Open(visaResource);
            io.WriteString("*IDN?");
            string idn = io.ReadString();
            Console.WriteLine($"Established the connection with {visaResource}.\n" +
                $"*IDN? query responce: {idn}");
        }
        ~VisaCommunicator()
        {
            io.IO.Close();
            System.Runtime.InteropServices.Marshal.ReleaseComObject(io);
            System.Runtime.InteropServices.Marshal.ReleaseComObject(rm);
        }

        public string Read()
        {
            return io.ReadString();
        }
        public string Query(string writeText)
        {
            io.WriteString(writeText);
            return io.ReadString();
        }
        public void Write(string writeText)
        {
            io.WriteString(writeText);
        }
        public void SetTimeout(double second)
        {
            io.IO.Timeout = (int)(second * 1000); // milliseconds
        }
        public int TimeoutSecond
        {
            get
            {
                return io.IO.Timeout / 1000; // milliseconds to seconds
            }
            set
            {
                io.IO.Timeout = value * 1000; // seconds to milliseconds
            }
        }
    }
#endif


#if NI
    // for NI GPIB-USB-HS
    // needs "National Instruments VisaNS" library
    public class VisaCommunicator : IVisaCommunicator
    {
        private NationalInstruments.VisaNS.MessageBasedSession mbSession;
        public VisaCommunicator(string visaResource)
        {
            mbSession =
                (NationalInstruments.VisaNS.MessageBasedSession)
                NationalInstruments.VisaNS.ResourceManager.
                GetLocalManager().Open(visaResource);
            string idn = mbSession.Query("*IDN?");
            Console.WriteLine($"Established the connection with{visaResource}.\n" +
                $"*IDN? query responce:{idn}");
        }
        public string Read()
        {
            return mbSession.ReadString();
        }
        public void Write(string writeText)
        {
            mbSession.Write(writeText);
        }
        public string Query(string writeText)
        {
            return mbSession.Query(writeText);
        }
        public void SetTimeout(double second) { throw new NotImplementedException(); }
        public int TimeoutSecond
        {
            get
            {
                return mbSession.Timeout/1000; // milliseconds to seconds 
            }

            set
            {
                mbSession.Timeout = value * 1000; // seconds to milliseconds
            }
        }
    }
#endif

    /// <summary>
    /// Use "NationalInstruments.VisaNS.MessageBasedSession" if available,
    /// else use "Ivi.Visa.Interop.FormattedIO488" if available,
    /// else throw an exception.
    /// </summary>
    /// <remarks>
    /// Hard to implement.
    /// Compile error (CS0256 ) if "National Instruments VisaNS" or
    /// "VISA COM 5.5 Type Library" is not available.
    /// </remarks>
    //public class VisaCommunicator : IVisaCommunicator
    //{
    //    string idn;
    //    public VisaCommunicator(string visaResource)
    //    {
    //        try
    //        {
    //            var mbSession =
    //                (NationalInstruments.VisaNS.MessageBasedSession)
    //                NationalInstruments.VisaNS.ResourceManager.
    //                GetLocalManager().Open(visaResource);
    //            idn = mbSession.Query("*IDN?");
    //            //string Read() { return mbSession.ReadString(); } // Wrong
    //            Console.WriteLine($"Established the connection with{visaResource}.\n" +
    //                $"*IDN? query responce:{idn}");
    //        }
    //        catch (Exception)
    //        {
    //            try
    //            {
    //                var rm = new Ivi.Visa.Interop.ResourceManager(); // error
    //                var io = new Ivi.Visa.Interop.FormattedIO488(); // error
    //                io.IO = (Ivi.Visa.Interop.IMessage)rm.Open(visaResource);
    //                io.WriteString("*IDN?");
    //                io.ReadString();
    //                io.IO.Close();
    //                System.Runtime.InteropServices.Marshal.ReleaseComObject(io);
    //                System.Runtime.InteropServices.Marshal.ReleaseComObject(rm);
    //                // establish NI VISA session
    //            }
    //            catch (Exception)
    //            {
    //                throw;
    //            }
    //        }
    //    }
    //}


}
