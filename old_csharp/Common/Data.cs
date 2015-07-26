using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Instr
{

    public class Data<T>
    {
        /// <summary>
        /// Row vectors
        /// { {x1, x2, x3, ...}, {y1, y2, y3, ...}, .. }
        /// </summary>
        private List<List<T>> _data = new List<List<T>>();
        public Data() { }
        public Data(T[][] matrix, bool isRowVectors = true)
        {
            if (isRowVectors)
            {
                foreach (T[] row in matrix)
                {
                    _data.Add(row.ToList());
                }
            }
            else // Transpose matrix
            {
                throw new NotImplementedException();
            }
        }

        //public override string ToString()
        //{
        //    return base.ToString();
        //}
    }
}