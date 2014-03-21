/**
 * @license
 * Copyright (C) 2010 The Libphonenumber Authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * @fileoverview  Phone Number Parser for agocontrol.
 *
 * @author Tanguy Bonneau
 *
 * @info To compile this file:
 *   - download source code from http://code.google.com/p/libphonenumber/
 *   - read javascript/README file
 *   - replace javascript/i18n/phonenumbers/demo.js by this file
 *   - compile javascript project (see README file)
 *   - update libphonenumber.js on agocontrol repository by javascript/i18n/phonenumbers/demo-compiled.js
 */

goog.require('goog.dom');
goog.require('goog.json');
goog.require('i18n.phonenumbers.PhoneNumberFormat');
goog.require('i18n.phonenumbers.PhoneNumberUtil');

function phoneNumberParser(phoneNumber, regionCode) {
  var $ = goog.dom.getElement;
  var out = {"error": false, "phone":null, "msg":""}
  try {
    var phoneUtil = i18n.phonenumbers.PhoneNumberUtil.getInstance();
    var number = phoneUtil.parseAndKeepRawInput(phoneNumber, regionCode);
    var isPossible = phoneUtil.isPossibleNumber(number);
    if (!isPossible)
    {
        out["error"] = true;
        out["msg"] = "impossible number (phonerNumber="+phoneNumber+", regionCode="+regionCode+")";
        return out;
    }
    else
    {
      var isNumberValid = phoneUtil.isValidNumber(number);
      if( !isNumberValid )
      {
        out["error"] = true;
        out["msg"] = "invalid number";
        return out;
      }
      else
      {
        var PNF = i18n.phonenumbers.PhoneNumberFormat;
        out["phone"] = phoneUtil.format(number, PNF.INTERNATIONAL);
        return out;
      }
    }
  } catch (e) {
    out["error"] = true;
    out["msg"] = "exception occurred ("+e+")";
    return out;
  }
}

goog.exportSymbol('phoneNumberParser', phoneNumberParser);
