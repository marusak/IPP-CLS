#!/usr/bin/python3
from __future__ import print_function
import sys
import re
import os

#TODO test ze za funkcoiu {};
#TODO test na prasaka naformatovane (ziadne medzery, vela medzier....)
#TODO test na class co sa vola myclass alebo classmine, class B{};class D{}
#TODO test kde identfikator bude Aa9_
#TODO test kde bude int x = 10;


#vytlaci chybovu hlasku a skonci
def error(message, error_code):
    print(message, file=sys.stderr);
    sys.exit(error_code);

#vytlaci pomoc a skonci
def help():
    print("HELP");#TODO more help
    exit(0);


#Parsuje argumenty z command_line
#berie bez nazvu skriptu
#vracia vsetky rozparsovane + pripadne implicitne hodnoty
def parseCommandLine(cmd_line):
    #TODO moze byt medzera v XPATH alebo mene suboru?
    #ak hej, je to problem pythonu
    result = {}
    for arg in cmd_line:
        matches = re.search("^--((\w|-)*)(=([^\s]+))?$", arg);
        if (matches == None):
            error("Dude, thats not even argument",1);
        if (matches.group(1) in result.keys()):
            error("Common, I already got it, no need to tell me twice",1)
        if (matches.group(1) not in ("help","input","output","pretty-xml","details","search","conflicts")):
            error("Holy moly, what was that?!",1)
        if (matches.group(4) == "" and matches.group(1) != "help" and matches.group(1) != "pretty-xml"):
            error("Input, output, details and search need som additional info",1);
        #TODO ak je 4orka None asi okrem pretty tak je to bug?
        result[matches.group(1)] = matches.group(4)
    return result

#vrati jeden token
#vracia zvysok,token
def getToken(acc):
    result = re.match("\s*(\w+|\{|\}|\(|\)|;|\=|,|:|\*|&)\s*([\s\S]*)",acc);
    if (result == None):
        error ("Token nepozna typ "+acc+"\n",69);
    return (result.group(1), result.group(2))

def getType(token, cls):
    acc_type = ""
    while True:#simulation do-while
        acc_type = acc_type + token
        token, cls = getToken(cls)
        if (token not in
            ("bool","char","int","float","double","void","wchar_t","signed","unsigned","short","long","*","&")):
            return (acc_type, token+" "+cls)
    

#berie cely vstup, rozprasuje ho na triedy a vlozi to do struktury
#Vracia dictonary : key = meno_triedy
#                   obsah = ?
def parseClasses(cls):
    while (cls != ""):
        token, cls = getToken(cls);
        if (token != "class"):
            error("Musi byt class",4);
        #name
        className, cls = getToken(cls);
        token, cls = getToken(cls);
        parents = ()
        methods = ()
        instances = ()
        while (token != "{"):
            #read the inheritance
            if (token in ("private", "protected", "public")):
                papaName, cls = getToken(cls);
                parents.append((papaName, token));
            else:
                parents.append((token, "private"));
            token, cls = getToken(cls)#comma, no control
            token, cls = getToken(cls)

        #implicitly private
        privacy = "private"
        token, cls = getToken(cls);
        #till the end of actuall class - one loop = one method or instance or privacy modifier
        while (token != "}"):
            if (token in ("private", "protected", "public")):
                privacy=token
                token, cls = getToken(cls);#:, no control
                token, cls = getToken(cls);
                continue
            #TODO virtual
            acc_type, cls  = getType(token, cls)#get type
            token, cls = getToken(cls)#get name
            acc_name = token;
            token, cls = getToken(cls);
            if (token == ";"):#instance declaration
                instances.append((acc_name, "declared"))
                token, cls = getToken(cls);
                continue
            if (token == "="):#instance definition
                while (token != ";"):
                    token, cls = getToken(cls)
                instances.append((acc_name, "defined"))
                token, cls = getToken(cls);
                continue
            if (token != "("):
                error("I dont know the input character "+token+" "+cls,69);
            #function declaration/definition
            #read arguments
            token, cls = getType(cls)
            function_arguments = ()
            while (token != ")"):
                arg, cls = getType(token, cls);#type
                name, cls = getToken(cls);#name
                token, cls = getToken(cls);#comma, no control
                token, cls = getToken(cls);#type of next argument or )
                function_arguments.append(arg, name)
            token, cls = getToken(cls)
            if (token == ";"):#method declaration
                methods.append((acc_name, function_arguments, "declared"))
                token, cls = getToken(cls);
                continue
            if (token == "="):#pure virtual
                token, cls = getToken(cls);#0 no control
                #TODO pure virtual
            if (token != "("):
                error("I dont know the input character "+token+" "+cls,69);



                    
















            virtual = false;
            if (token == "virtual"):
                virtual = true;







        
        






def main():
    parsed = parseCommandLine(sys.argv[1:]);
    keys = parsed.keys();
    if ("help" in keys):
        if (len(keys) != 1):
            error("Kombinovat --help a ine argumenty sa nepatri", 1)
        help();
    if ("input" not in keys):
        inputStream = sys.stdin;
    else:
        try:
            inputStream = open(parsed["input"],"r");
        except:
            error("Input file is not valid or readable",2)
    inputContent = inputStream.read()
    parsedClasses = parseClasses(inputContent);



main()
    


