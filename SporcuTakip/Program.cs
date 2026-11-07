using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace SporcuTakip
{
    internal static class Program
    {
        /// <summary>
        /// Uygulamanın ana girdi noktası.
        /// </summary>
        [STAThread]
        static void Main()
        {


            //try
            //{
            //    SQLitePCL.Batteries_V2.Init();
            //}
            //catch { }

          //  try { SQLitePCL.Batteries_V2.Init(); } catch { }   // <-- kritik
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Form1());

        }

    }
}
