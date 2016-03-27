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
#TODO test kde bude deklaracie class a kusok neskor aj definicia tej class + opace
#TODO test na static
#TODO test na konstuktor a destruktor


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
    if (result.group(1) == ":" and result.group(2)[0] == ":"):#:: operator
        return ("::", result.group(2)[1:])
    else:
        return (result.group(1), result.group(2))

def getType(token, cls):
    acc_type = ""
    while True:#simulation do-while
        acc_type = acc_type + token
        token, cls = getToken(cls)
        if (token not in
            ("void","bool","char","int","float","double","void","wchar_t","signed","unsigned","short","long","*","&")):
            return (acc_type, token+" "+cls)
    

#berie cely vstup, rozprasuje ho na triedy a vlozi to do struktury
#Returns list of classes, where each class consists from:
#   [0] = name
#   [1] = list of parents (ClassName, type)
#   [2] = methods (Name, return_type, arguments, defined/declared. virtual, pureVirtual, privacy,
#   static)
#   [3] = instances (Name, type, defined/declared, virtual, privacy, static)
#   [4] = usings (from, what, privacy)
def parseClasses(cls):
    #TODO konstruktor, destruktor
    classes = []
    while (cls != ""):
        token, cls = getToken(cls);
        if (token != "class"):
            error("Musi byt class",4);
        #name
        className, cls = getToken(cls);
        token, cls = getToken(cls);
        parents = []
        methods = []
        instances = []
        usings = []
        while (token != "{" and token != ";"):
            token, cls = getToken(cls)#comma, no control
            #read the inheritance
            if (token in ("private", "protected", "public")):
                papaName, cls = getToken(cls);
                parents.append((papaName, token));
            else:
                parents.append((token, "private"));
            token, cls = getToken(cls)

        #declaration -> moze sposobit problemy len v takejto forme
        if (token == ";"):#only class declaration
            keys = [i[0] for i in classes]
            if (className in keys):#uz mame danu triedu vnutri
                classes.append = (className, "declared")
            

        #implicitly private
        privacy = "private"
        token, cls = getToken(cls);
        #till the end of actuall class - one loop = one method or instance or privacy modifier
        while (token != "}"):
            virtual = False;
            static = False;
            if (token == "virtual"):
                virtual = True;
                token, cls = getToken(cls)
            if (token == "static"):
                static = True;
                token, cls = getToken(cls)

            if (token in ("private", "protected", "public")):
                privacy=token
                token, cls = getToken(cls);#:, no control
                token, cls = getToken(cls);
                continue
            if (token == "using"):
                fromName, cls = getToken(cls)
                token, cls = getToken(cls)#::
                whatName, cls = getToken(cls)
                token, cls = getToken(cls)#;
                token, cls = getToken(cls)
                usings.append((fromName, whatName, privacy))
                continue
            acc_type, cls  = getType(token, cls)#get type
            token, cls = getToken(cls)#get name
            acc_name = token;
            token, cls = getToken(cls);
            if (token == ";"):#instance declaration
                instances.append((acc_name, acc_type, "declared",virtual, privacy, static))
                token, cls = getToken(cls);
                continue
            if (token == "="):#instance definition
                while (token != ";"):
                    token, cls = getToken(cls)
                instances.append((acc_name, acc_type, "defined",virtual, privacy, static))
                token, cls = getToken(cls);
                continue
            if (token != "("):
                error("I dont know the input character "+token+" "+cls,69);
            #function declaration/definition
            #read arguments
            token, cls = getToken(cls)
            function_arguments = []
            while (token != ")"):
                arg, cls = getType(token, cls);#type
                if (arg == "void"):
                    name, cls = getToken(cls);#)
                    break;
                name, cls = getToken(cls);#name
                token, cls = getToken(cls);#comma or )
                function_arguments.append((arg, name))
            token, cls = getToken(cls)
            if (token == ";"):#method declaration
                methods.append((acc_name, acc_type, function_arguments,
                    "declared",virtual,False,privacy, static))
                token, cls = getToken(cls);
                continue
            if (token == "="):#pure virtual
                token, cls = getToken(cls);#0 no control
                token, cls = getToken(cls);#; no control
                methods.append((acc_name, acc_type, function_arguments,
                    "declared",virtual,True,privacy, static))
                token, cls = getToken(cls);
                continue
            if (token != "{"):
                error("I dont know the input character1 "+token+" "+cls,69);
            token, cls = getToken(cls);#;
            methods.append((acc_name, acc_type, function_arguments, "defined",virtual,
                False,privacy, static))
            token, cls = getToken(cls);
        token, cls = getToken(cls); #} or another class
        keys = [i[0] for i in classes]
        if (className in keys):#uz mame danu triedu vnutri
            adept = [x for x in classes if x[1]== "declared"]
            if adept:
                n = classes.index(adept)
                classes[n] = (className, parents, methods, instances, usings )
        else:
            classes.append((className, parents, methods, instances, usings ))

    return classes


#berie si rozparsovane funckie
#vrati novu strukturu (podobnu tu z parsovania), ale zdene metody a instacie uz budu ramci kazdej
#   triedy zvlast
def makeClassesComplete(classes):
    pass


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
    for item in parsedClasses:
        print("\nclass----\n")
        print(item)


main()
    


