
namespace Instr
{
    public class SussPA300 : VisaCommunicator
    {
        // -- Referrence --
        // PBRemote.chm
        // ProberBench 6 Command and Interface Reference
        // - GPIB Interface
        // - Kernel Commands
        // 
        // *IDN?
        // 
        // ReadChuckPosition
        // ReadChuck Heights
        // MoveChuckSeparation
        // MoveChuckContact
        // 
        // MoveChuckIndex
        public SussPA300(string visaResource) : base(visaResource)
        {
            return;
        }

    }
}
