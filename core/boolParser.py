#!/usr/bin/env python

import re

class BoolParser:
    def parse(self, str, criteria):
        if not str.startswith("("):
            str = "(" + str + ")"
        return bool(self.parseGroup(str, criteria))

    def getCriteriaIdx(self, str):
        p = re.compile(".+([0-9]).+")
        match = p.match(str)
        return match.groups()[0]

    def parseGroup(self, str, criteria):
        remove_p = re.compile("(^\()|(\)$)")
        str = remove_p.sub("", str)
        p = re.compile("(and|or)")
        type = None
        data = p.split(str)
        expr = []
        for i in range(len(data)):
            substr = data[i]
            if substr == "and" or substr == "or":
                type = substr
                continue
            if substr.strip().startswith("("):
                next = ""
                for j in range(i, len(data)):
                    next += data[j]
                expr.append(self.parseGroup(remove_p.sub("", next.strip()), criteria))
                break

            if substr.strip() == "True":
                expr.append(1)
            elif substr.strip() == "False":
                expr.append(0)
            else:
                expr.append(criteria[self.getCriteriaIdx(substr)])
            
            if not type == None:
                if type == "and":
                    expr = [reduce(lambda x,y : x and y, expr)]
                else:
                    expr = [reduce(lambda x,y : x or y, expr)]


        if type == "and":
            return reduce(lambda x,y : x and y, expr)
        elif type == "or":
            return reduce(lambda x,y : x or y, expr)
        elif len(expr) == 1:
            return expr[0]
        else:
            raise "Failed to parse boolean string"
