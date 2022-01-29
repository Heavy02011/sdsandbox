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
            // input string
            string input = "Parking Lot Nerds " + "\uD83C\uDFF4\u200D\u2620\uFE0F";

            // sample unicode strings
            string flag_france  = "🇫🇷";
            string flag_pirate  = Encoding.UTF8.GetString(Encoding.Default.GetBytes("\uD83C\uDFF4\u200D\u2620\uFE0F"));
            string flag_usa     = Encoding.UTF8.GetString(Encoding.Default.GetBytes("\U0001F1FA\U0001F1F8"));
            string umbrella_str = Char.Parse("\u2602").ToString();

            // create sample pacman as UTF32 unicode string
            string pacman_utf32 = "";
            pacman_utf32 += Char.Parse("\uD83D").ToString();
            pacman_utf32 += Char.Parse("\uDE00").ToString();
                        
            // test output
            Console.WriteLine("Hello World!\n");
            Console.WriteLine("Interactive Unicode Demo:" + input);
            Console.WriteLine("testing" + umbrella_str + flag_france + flag_pirate);
            Console.WriteLine("Pacman: " + pacman_utf32);
            Console.WriteLine("USA: " + flag_usa);

            // test input
            /*
            Console.WriteLine("\n\nEnter some text: ");
            string input = Console.ReadLine();
            Console.WriteLine("You entered: " + input);
            Console.WriteLine(SplitUnicode(input));
            */

        }

        // create a function that loops through a string of uinicode values and split them "\u"
        /*
        public static string[] SplitUnicode(string input)
        {
            string[] output = input.Split(new string[] { "\u" }, StringSplitOptions.None);
            return output;
        }
        */

    }
}
