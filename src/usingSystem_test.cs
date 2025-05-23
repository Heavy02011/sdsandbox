/*
(sds15) rainer@neuron:/media/rainer/_data/30-projects/donkeycar-dev_heavy02011/sdsandbox/src$ 

// compile
mcs -out:usingdSystem_test.exe usingSystem_test.cs

// run
mono usingdSystem_test.exe

*/

using System;
using System.Text;

class Example
{
   static void Main()
   {

      //string  flag_pirate = Encoding.UTF8.GetString(Encoding.Default.GetBytes("\uD83C\uDFF4\u200D\u2620\uFE0F"));
      //string  umbrella_str = Char.Parse("\u2602").ToString();
      // string unicodeString = "This string contains the unicode character Pi (\u03a0)";
      string unicodeString = "my car name Pi (\u03a0) with sample \uD83C\uDFF4\u200D\u2620\uFE0F and  this \u2602";

      // Create two different encodings.
      Encoding ascii = Encoding.ASCII;
      Encoding unicode = Encoding.Unicode;

      // Convert the string into a byte array.
      byte[] unicodeBytes = unicode.GetBytes(unicodeString);

      // Perform the conversion from one encoding to the other.
      byte[] asciiBytes = Encoding.Convert(unicode, ascii, unicodeBytes);
         
      // Convert the new byte[] into a char[] and then into a string.
      char[] asciiChars = new char[ascii.GetCharCount(asciiBytes, 0, asciiBytes.Length)];
      ascii.GetChars(asciiBytes, 0, asciiBytes.Length, asciiChars, 0);
      string asciiString = new string(asciiChars);

      // Display the strings created before and after the conversion.
      Console.WriteLine("Original string: {0}", unicodeString);
      Console.WriteLine("Ascii converted string: {0}", asciiString);
         
      string input = "Parking Lot Nerds racing on Pi (\u03a0) with sample \uD83C\uDFF4\u200D\u2620\uFE0F and  this \u2602";
      string output = ParseUnicodeString(input);
      Console.WriteLine(input);
      Console.WriteLine(output);
   }

   // create a function to convert a string containing unicode characters to a string containing ascii characters
   // source: https://docs.microsoft.com/en-us/dotnet/api/system.text.encoding.convert?redirectedfrom=MSDN&view=net-6.0#System_Text_Encoding_Convert_System_Text_Encoding_System_Text_Encoding_System_Byte___
   public static string ParseUnicodeString(string unicodeString)
   {

         // Create two different encodings.
         Encoding ascii = Encoding.ASCII;
         Encoding unicode = Encoding.Unicode;

         // Convert the string into a byte array.
         byte[] unicodeBytes = unicode.GetBytes(unicodeString);

         // Perform the conversion from one encoding to the other.
         byte[] asciiBytes = Encoding.Convert(unicode, ascii, unicodeBytes);
            
         // Convert the new byte[] into a char[] and then into a string.
         char[] asciiChars = new char[ascii.GetCharCount(asciiBytes, 0, asciiBytes.Length)];
         ascii.GetChars(asciiBytes, 0, asciiBytes.Length, asciiChars, 0);
         string asciiString = new string(asciiChars);

         // Convert the new byte[] into a char[] and then into a string.
         char[] unicodeChars = new char[unicode.GetCharCount(unicodeBytes, 0, unicodeBytes.Length)];
         unicode.GetChars(unicodeBytes, 0, unicodeBytes.Length, unicodeChars, 0);
         string unicodeString_out = new string(unicodeChars);


         // Display the strings created before and after the conversion.
         Console.WriteLine("Original string: {0}", unicodeString);
         Console.WriteLine("Ascii converted string: {0}", asciiString);
      return unicodeString_out;
   }



}
// The example displays the following output:
//    Original string: This string contains the unicode character Pi (Π)
//    Ascii converted string: This string contains the unicode character Pi (?)



