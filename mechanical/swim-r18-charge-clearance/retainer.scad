cuts=[[[19.9, -5.8, 1.4000000000000004], [1.5, 4.4, 3]], [[19.9, 3.5, 1.4000000000000004], [1.5, 4.9, 3]]];

part="retainer";
module old(){import("../swim-r11-thermal-fit/retainer.stl");}
module revised(){difference(){old();for(c=cuts)translate(c[0])cube(c[1]);}}
if(part=="added_material")difference(){revised();old();}
else if(part=="removed_material")difference(){old();revised();}
else revised();
