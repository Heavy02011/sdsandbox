using System;
using System.IO;
using System.Text;

/*
(sds15) rainer@neuron:/media/rainer/_data/30-projects/donkeycar-dev_heavy02011/sdsandbox/src$ 

// compile
mcs -out:test_unicode.exe test_unicode.cs

// run
mono test_unicode.exe

*/

namespace ConsoleApplication
{
    public class Program
    {
        public static void Main(string[] args)
        {
            // sample unicode strings
            string flag_france  = "🇫🇷";
            string flag_pirate  = Encoding.UTF8.GetString(Encoding.Default.GetBytes("\uD83C\uDFF4\u200D\u2620\uFE0F"));
            string umbrella_str = Char.Parse("\u2602").ToString();

            // test output
            Console.WriteLine("Interactive Unicode Demo");
            Console.WriteLine("Parking Lot Nerds" + umbrella_str + flag_france + flag_pirate);


            Console.WriteLine("Hello World!");
        }
    }
}
