from fnmatch import fnmatchcase
import re

valueRE = re.compile(r'[=*+-]\d+')

class Parameters(object):
    """Game play parameters.
    These are variables represent the "settings" of a game, not the state
    So, for example, the players maxHealth is a parameter but their actual health isn't.

    Parameters can be influenced by effects which come and go.
    How these changing values impact the game play is not the responsibility of this class
    but it does offer a listener system to be notified when a value changes
    """
    def __init__(self):
        self.listeners = []
        self.parameters = {}
        self.__addParameter("player.maxHealth", 100)
        self.__addParameter("gun.damage", 2)

    def __addParameter(self, name, baseValue):
        self.parameters[name] = Parameter(baseValue)

    def _addEffect(self, parameterName, qualifierPattern, id, value):
        if not valueRE.match(value):
            raise MalformedValueError(value)

        self.parameters[parameterName].addEffect(qualifierPattern, id, value)

        self._notifyListeners(parameterName, qualifierPattern)

    def _removeEffect(self, parameterName, id):
        e = self.parameters[parameterName].removeEffect(id)

        self._notifyListeners(parameterName, e.qualifierPattern)

    def _getValue(self, parameterName, qualifier):
        return self.parameters[parameterName].value(qualifier)

    def _subscribeToValue(self, parameterNamePattern, qualifierPattern, listener):
        self.listeners.append((parameterNamePattern, qualifierPattern, listener))

    def _notifyListeners(self, parameterName, listenerQualifierPattern):
        for (parameterNamePattern, qualifierPattern, listener) in self.listeners:
            #check qualifiers both ways round as either pattern could be broader than the other
            #TODO: This doesn't cover the fact that '*/1' and '1/*' should match
            #https://stackoverflow.com/a/3213301/6950 for a better algorithm
            qualifierMatches = fnmatchcase(listenerQualifierPattern, qualifierPattern) or fnmatchcase(qualifierPattern, listenerQualifierPattern)
            if fnmatchcase(parameterName, parameterNamePattern) and qualifierMatches:
                listener(parameterName)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "Parameters(%s)" % (",".join(self.parameters),)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def getPlayerValue(self, parameterName, teamID, playerID):
        """Convenience function for getting a parameter value for a particular player."""
        return self._getValue("player." + parameterName, str(teamID) + "/" + str(playerID))

    def addPlayerEffect(self, parameterName, teamID, playerID, id, value):
        """Convenience function for adding an effect for a particular player."""
        self._addEffect("player." + parameterName, str(teamID) + "/" + str(playerID), id, value)

    def addTeamEffect(self, parameterName, teamID, id, value):
        """Convenience function for adding an effect for every player on a particular team."""
        self._addEffect("player." + parameterName, str(teamID) + "/*", id, value)

    def getPlayerParameters(self, teamID, playerID):
        """
        Get all of the parameters and effects for a given player
        This looks like a filtered version of toSimpleTypes
        """
        out = {}
        for pName in self.parameters:
            out[pName] = self.parameters[pName].getQualifiedParameter(str(teamID) + "/" + str(playerID))

        return { 'parameters': out }

    #TODO: filter to just a single player's effects.
    def toSimpleTypes(self):
        """encode as JSON"""
        out = {}
        for pName in self.parameters:
            out[pName] = self.parameters[pName].toSimpleTypes()

        return { 'parameters': out }

    @classmethod
    def fromSimpleTypes(cls, input):
        if isinstance(input, dict):
            obj = Parameters()
            for pName in input['parameters']:
                obj.parameters[pName] = Parameter.fromSimpleTypes(input['parameters'][pName])

            return obj
        else:
            raise ValueError('Parameters should be deserialised from a dict not a ' + type(input))


class MalformedValueError(RuntimeError):
    def __init__(self, val):
      self.val = val

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "MalformedValueError(%s)" % (self.val,)


class Parameter(object):
    def __init__(self, baseValue):
        self.baseValue = baseValue
        self.effects = []

    @classmethod
    def fromSimpleTypes(cls, input):
        if isinstance(input, dict):
            obj = Parameter(input['baseValue'])
            obj.effects = [Effect.fromSimpleTypes(e) for e in input['effects']]
            return obj
        else:
            raise ValueError('Parameter should be deserialised from a dict not a ' + type(input))

    def toSimpleTypes(self):
        return {
            'baseValue': self.baseValue,
            'effects': [e.toSimpleTypes() for e in self.effects]
        }

    def getQualifiedParameter(self, qualifier):
        """Serialise this parameter including only the effects which cover the given qualifier"""
        return {
            'baseValue': self.baseValue,
            'effects': [e.toSimpleTypes() for e in self.effects if e.appliesTo(qualifier)]
        }

    def value(self, qualifier):
        val = self.baseValue
        for effect in self.effects:
            val = effect.apply(val, qualifier)
        return val

    def addEffect(self, qualifierPattern, id, value):
        self.effects.append(Effect(qualifierPattern, id, value))

    def removeEffect(self, id):
        removed = [e for e in self.effects if e.id == id]
        self.effects = [e for e in self.effects if e.id != id]
        return removed[0]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "Parameter(%s, (%s))" % (self.baseValue, ",".join(self.effects), )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Effect(object):
    def __init__(self, qualifierPattern, id, value):
        self.qualifierPattern = qualifierPattern
        self.id = id
        self.value = value

    @classmethod
    def fromSimpleTypes(cls, input):
        if isinstance(input, dict):
            return Effect(input['qualifierPattern'], input['id'], input['value'])
        else:
            raise ValueError('Effect should be deserialised from a dict not a ' + type(input))

    def toSimpleTypes(self):
        return self.__dict__

    def appliesTo(self, qualifier):
        return fnmatchcase(qualifier, self.qualifierPattern)

    def apply(self, val, qualifier):
        if self.appliesTo(qualifier):
            op = self.value[0]
            arg = int(self.value[1:])

            if op == '=':
                return arg
            elif op == '*':
                return val * arg
            elif op == '+':
                return val + arg
            elif op == '-':
                return val - arg
        else:
            #This isn't covered by the qualifier so don't change the val.
            return val

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s(%s, %s)" % (self.value, self.id, self.qualifierPattern, )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
