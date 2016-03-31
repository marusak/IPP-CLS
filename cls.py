# !/usr/bin/python3
# coding=utf-8
"""xmarus06 STUFF."""
from __future__ import print_function
import sys
import re

# TODO test ze za funkcoiu {}
# TODO test na prasaka naformatovane (ziadne medzery, vela medzier....)
# TODO test na class co sa vola myclass alebo classmine, class B{}class D{}
# TODO test kde identfikator bude Aa9_
# TODO test kde bude int x = 10
# TODO test kde bude deklaracie class a kusok neskor aj def tej classvv
# TODO test na static
# TODO test na konstuktor a destruktor
# TODO clenska premenna typu class


def error(message, error_code):
    """Print exit message to stderr and exit."""
    print(message, file=sys.stderr)
    sys.exit(error_code)


def help():
    """Print help and exit."""
    print("HELP")  # TODO more help
    exit(0)


# Parsuje argumenty z command_line
# berie bez nazvu skriptu
# vracia vsetky rozparsovane + pripadne implicitne hodnoty
def parseCommandLine(cmd_line):
    """Parse command line.

    cmd_line: list of arguments without script name
    return :
    """
    result = {}
    for arg in cmd_line:
        matches = re.search("^--((\w|-)*)(=([^\s]+))?$", arg)
        if (matches is None):
            error("Dude, thats not even argument", 1)
        if (matches.group(1) in result.keys()):
            error("Common, I already got it, no need to tell me twice", 1)
        if (matches.group(1) not in ("help", "input", "output", "pretty-xml",
           "details", "search", "conflicts")):
            error("Holy moly, what was that?!", 1)
        if (matches.group(4) == "" and matches.group(1) != "help" and
           matches.group(1) != "pretty-xml"):
            error("I/O, details and search need som additional info", 1)
        # TODO ak je 4orka None asi okrem pretty tak je to bug?
        result[matches.group(1)] = matches.group(4)
    return result


def getToken(acc):
    """Return one token."""
    result = re.match("\s*(\w+|\{|\}|\(|\)||\=|,|:|\*|&)\s*([\s\S]*)", acc)
    if (result is None):
        error("Token nepozna typ "+acc+"\n", 69)
    if (result.group(1) == ":" and result.group(2)[0] == ":"):  # ::
        return ("::", result.group(2)[1:])
    else:
        return (result.group(1), result.group(2))


def getType(token, cls):
    """Return type of variable or function."""
    acc_type = ""
    while True:  # simulation do-while
        acc_type = acc_type + token
        token, cls = getToken(cls)
        if (token not in
            ("void", "bool", "char", "int", "float", "double", "void",
             "wchar_t", "signed", "unsigned", "short", "long", "*", "&")):
            return (acc_type, token+" "+cls)


def parseClasses(cls):
    """Berie cely vstup, rozprasuje ho na triedy a vlozi to do struktury.

    Returns list of classes, where each class consists from:
    key = name
    [0] = list of parents (ClassName, type)
    [1] = methods (Name, return_type, arguments, defined/declared,
        virtual, pureVirtual, privacy, static)
    [2] = instances(Name, type, defined/declared, virtual, privacy, static)
    [3] = usings (from, what, privacy)
    """
    # TODO konstruktor, destruktor
    classes = {}
    while (cls != ""):
        token, cls = getToken(cls)
        if (token != "class"):
            error("Musi byt class", 4)
        # name
        className, cls = getToken(cls)
        token, cls = getToken(cls)
        parents = {}
        methods = {}
        instances = {}
        usings = {}
        while (token != "{" and token != ""):
            token, cls = getToken(cls)  # comma, no control
            # read the inheritance
            if (token in ("private", "protected", "public")):
                papaName, cls = getToken(cls)
                parents[papaName] = token
            else:
                parents[token] = "private"
            token, cls = getToken(cls)

        # declaration -> moze sposobit problemy len v takejto forme
        if (token == ""):  # only class declaration
            if (className not in classes.keys()):
                classes[className] = "declared"
                continue
            else:
                continue

        # implicitly private
        privacy = "private"
        token, cls = getToken(cls)
        # till the end of actuall class
        # one loop = one method or instance or privacy modifier
        while (token != "}"):
            virtual = False
            static = False
            if (token == "virtual"):
                virtual = True
                token, cls = getToken(cls)
            if (token == "static"):
                static = True
                token, cls = getToken(cls)

            if (token in ("private", "protected", "public")):
                privacy = token
                token, cls = getToken(cls)  # :, no control
                token, cls = getToken(cls)
                continue
            if (token == "using"):
                fromName, cls = getToken(cls)
                token, cls = getToken(cls)  # ::
                whatName, cls = getToken(cls)
                token, cls = getToken(cls)  # " "
                token, cls = getToken(cls)
                usings[fromName] = (whatName, privacy)
                continue
            acc_type, cls = getType(token, cls)  # get type
            token, cls = getToken(cls)  # get name
            acc_name = token
            token, cls = getToken(cls)
            if (token == ""):  # instance declaration
                instances[acc_name] = (acc_type, "declared",
                                       virtual, privacy, static)
                token, cls = getToken(cls)
                continue
            if (token == "="):  # instance definition
                while (token != ""):
                    token, cls = getToken(cls)
                instances[acc_name] = (acc_type, "defined",
                                       virtual, privacy, static)
                token, cls = getToken(cls)
                continue
            if (token != "("):
                error("I dont know the input character "+token+" "+cls, 70)
            # function declaration/definition
            # read arguments
            token, cls = getToken(cls)
            function_arguments = []
            while (token != ")"):
                arg, cls = getType(token, cls)  # type
                if (arg == "void"):
                    name, cls = getToken(cls)  # )
                    break
                name, cls = getToken(cls)  # name
                token, cls = getToken(cls)  # comma or )
                function_arguments.append((arg, name))
            token, cls = getToken(cls)
            if (token == ""):  # method declaration
                methods[acc_name] = (acc_type, function_arguments, "declared",
                                     virtual, False, privacy, static)
                token, cls = getToken(cls)
                continue
            if (token == "="):  # pure virtual
                token, cls = getToken(cls)  # 0 no control
                token, cls = getToken(cls)  # no control
                methods[acc_name] = (acc_type, function_arguments, "declared",
                                     virtual, True, privacy, static)
                token, cls = getToken(cls)
                continue
            if (token != "{"):
                error("I dont know the input character1 "+token+" "+cls, 69)
            token, cls = getToken(cls)  # " "
            methods[acc_name] = (acc_type, function_arguments, "defined",
                                 virtual, False, privacy, static)
            token, cls = getToken(cls)
        token, cls = getToken(cls)  # } or another class
        if (className in classes.keys()):  # uz mame danu triedu vnutri
            if (classes[className] == "declared"):
                classes[className] = (parents, methods, instances, usings)
            else:
                error("redefinicia triedy", 4)
        else:
            classes[className] = (parents, methods, instances, usings)

    return classes


def makeClassesComplete(cs):
    """Fill inhereted classes methods and instances.

    cs: output from parseClasses
    """
    for key in cs.keys():
        if (cs[key][0] == {}):  # no parents
            continue
        print ("adding to  "+key)
        for parent in cs[key][0]:
            print (parent)


def main():
    """Main."""
    parsed = parseCommandLine(sys.argv[1:])
    keys = parsed.keys()
    if ("help" in keys):
        if (len(keys) != 1):
            error("Kombinovat --help a ine argumenty sa nepatri", 1)
        help()
    if ("input" not in keys):
        inputStream = sys.stdin
    else:
        try:
            inputStream = open(parsed["input"], "r")
        except:
            error("Input file is not valid or readable", 2)
    inputContent = inputStream.read()
    parsedClasses = parseClasses(inputContent)
    for item in parsedClasses.keys():
        print(item)
        print(parsedClasses[item])
    print ("----------------------------------------------------------------")
    makeClassesComplete(parsedClasses)
main()
