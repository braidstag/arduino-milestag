from fnmatch import fnmatchcase
import re

valueRE = re.compile(r'[=*+-]\d+')
empty_or_all_wildcards = re.compile(r'^\**$')


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

    def __addParameter(self, name, base_value):
        self.parameters[name] = Parameter(base_value)

    def _addEffect(self, parameter_name, qualifier_pattern, effect_id, value):
        if not valueRE.match(value):
            raise MalformedValueError(value)

        self.parameters[parameter_name].addEffect(qualifier_pattern, effect_id, value)

        self._notifyListeners(parameter_name, qualifier_pattern)

    def _removeEffect(self, parameter_name, effect_id):
        e = self.parameters[parameter_name].removeEffect(effect_id)

        self._notifyListeners(parameter_name, e.qualifierPattern)

    def _getValue(self, parameter_name, qualifier):
        return self.parameters[parameter_name].value(qualifier)

    def _subscribeToValue(self, parameter_name_pattern, qualifier_pattern, listener):
        self.listeners.append((parameter_name_pattern, qualifier_pattern, listener))

    def _notifyListeners(self, parameter_name, listener_qualifier_pattern):
        for (parameterNamePattern, qualifierPattern, listener) in self.listeners:
            if fnmatchcase(parameter_name, parameterNamePattern) and self._qualifierMatches(qualifierPattern, listener_qualifier_pattern):
                listener(parameter_name)

    # algorithm from https://stackoverflow.com/a/3213301/6950
    def _qualifierMatches(self, g1, g2):
        if len(g1) == 0:
            return bool(empty_or_all_wildcards.match(g2))
        if len(g2) == 0:
            return bool(empty_or_all_wildcards.match(g1))

        c1 = g1[0]
        t1 = g1[1:]
        c2 = g2[0]
        t2 = g2[1:]
        if c1 == '*' or c2 == '*':
            return self._qualifierMatches(g1, t2) or self._qualifierMatches(t1, g2)

        return c1 == c2 and self._qualifierMatches(t1, t2)

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

    def getPlayerValue(self, parameter_name, team_id, player_id):
        """Convenience function for getting a parameter value for a particular player."""
        return self._getValue("player." + parameter_name, str(team_id) + "/" + str(player_id))

    def addPlayerEffect(self, parameter_name, team_id, player_id, effect_id, value):
        """Convenience function for adding an effect for a particular player."""
        self._addEffect("player." + parameter_name, str(team_id) + "/" + str(player_id), effect_id, value)

    def addTeamEffect(self, parameter_name, team_id, effect_id, value):
        """Convenience function for adding an effect for every player on a particular team."""
        self._addEffect("player." + parameter_name, str(team_id) + "/*", effect_id, value)

    def getPlayerParameters(self, team_id, player_id):
        """
        Get all of the parameters and effects for a given player
        This looks like a filtered version of toSimpleTypes
        """
        out = {}
        for pName in self.parameters:
            out[pName] = self.parameters[pName].getQualifiedParameter(str(team_id) + "/" + str(player_id))

        return {'parameters': out}

    def toSimpleTypes(self):
        """encode as JSON"""
        out = {}
        for pName in self.parameters:
            out[pName] = self.parameters[pName].toSimpleTypes()

        return {'parameters': out}

    @classmethod
    def fromSimpleTypes(cls, input_obj):
        if isinstance(input_obj, dict):
            obj = Parameters()
            for pName in input_obj['parameters']:
                obj.parameters[pName] = Parameter.fromSimpleTypes(input_obj['parameters'][pName])

            return obj
        else:
            raise ValueError('Parameters should be deserialised from a dict not a ' + type(input_obj))


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
    def fromSimpleTypes(cls, input_obj):
        if isinstance(input_obj, dict):
            obj = Parameter(input_obj['baseValue'])
            obj.effects = [Effect.fromSimpleTypes(e) for e in input_obj['effects']]
            return obj
        else:
            raise ValueError('Parameter should be deserialised from a dict not a ' + type(input_obj))

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

    def addEffect(self, qualifierPattern, effect_id, value):
        self.effects.append(Effect(qualifierPattern, effect_id, value))

    def removeEffect(self, effect_id):
        removed = [e for e in self.effects if e.id == effect_id]
        self.effects = [e for e in self.effects if e.id != effect_id]
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
    def __init__(self, qualifierPattern, effect_id, value):
        self.qualifierPattern = qualifierPattern
        self.id = effect_id
        self.value = value

    @classmethod
    def fromSimpleTypes(cls, input_object):
        if isinstance(input_object, dict):
            return Effect(input_object['qualifierPattern'], input_object['id'], input_object['value'])
        else:
            raise ValueError('Effect should be deserialised from a dict not a ' + type(input_object))

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
            # This isn't covered by the qualifier so don't change the val.
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
