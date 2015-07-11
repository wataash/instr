using System;

namespace Instr
{
    public interface IVisaCommunicator
    {
        string Read();
        void Write(string writeText);
        string Query(string writeText);
        void SetTimeout(double second);
    }

    // Example for Agilent 82357A
    // needs VISA COM 5.5 Type Library
    public class AgilentVisaCommunicator : IVisaCommunicator
    {
        private Ivi.Visa.Interop.ResourceManager rm;
        private Ivi.Visa.Interop.FormattedIO488 io;
        public AgilentVisaCommunicator(string visaResource)
        {
            rm = new Ivi.Visa.Interop.ResourceManager();
            io = new Ivi.Visa.Interop.FormattedIO488();
            io.IO = (Ivi.Visa.Interop.IMessage)rm.Open(visaResource);
            io.WriteString("*IDN?");
            string idn = io.ReadString();
            Console.WriteLine("Established the connection with " + visaResource + ".\n" +
                "*IDN? query responce: " + idn);
        }
        ~AgilentVisaCommunicator()
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
            io.IO.Timeout = (int)(second * 1000); // millisecond
        }
    }

    public class NIVisaCommunicator : IVisaCommunicator
    {
        public string Read()
        {
            throw new NotImplementedException();
        }
        public void Write(string writeText)
        {
            throw new NotImplementedException();
        }
        public string Query(string writeText)
        {
            throw new NotImplementedException();
        }
        public void SetTimeout(double second)
        {
            throw new NotImplementedException();
        }
    }

    // Error: if IVI library is not available (CS0256)
    //
    // Use Ivi.Visa.Interop.FormattedIO488 if available,
    // else use NationalInstruments.VisaNS.MessageBasedSession if available,
    // else throw exception.
    //
    //public class VisaCommunicator : IVisaCommunicator
    //{
    //    private bool hasDummyLib, hasIviLib, hasNILib;
    //    public VisaCommunicator(string visaResource)
    //    {
    //        try
    //        {
    //            var rm = new Ivi.Visa.Interop.ResourceManager(); // error
    //            var io = new Ivi.Visa.Interop.FormattedIO488(); // error
    //            io.IO = (Ivi.Visa.Interop.IMessage)rm.Open(visaResource);
    //            io.WriteString("*IDN?");
    //            io.ReadString();
    //            io.
    //            io.IO.Close();
    //            System.Runtime.InteropServices.Marshal.ReleaseComObject(io);
    //            System.Runtime.InteropServices.Marshal.ReleaseComObject(rm);
    //            hasIviLib = true;
    //        }
    //        catch (Exception)
    //        {
    //            try
    //            {
    //                // establish NI VISA session
    //            }
    //            catch (Exception)
    //            {

    //                throw;
    //            }
    //            throw;
    //        }
    //    }
    //    public string Query(string writeText)
    //    {
    //        throw new NotImplementedException();
    //    }
    //    public string Read()
    //    {
    //        throw new NotImplementedException();
    //    }
    //    public void Write(string writeText)
    //    {
    //        throw new NotImplementedException();
    //    }
    //}
}
