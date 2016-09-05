/*
 * Project Wok
 *
 * Copyright IBM Corp, 2016
 *
 * Code derived from Project Kimchi
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
wok.session = {

	remaingTimeToShowAlert: 30000,
	remainingSessionTime: null,
	flagInTimer: false,
	expiringTimeout: null,
	oneSecondExternalCounter: null,
	oneSecondInternalCounter: null,

	expiringCounter: function(){
		var counter = wok.session.remainingSessionTime - wok.session.remaingTimeToShowAlert;
		if (!isNaN(counter)) {
			wok.session.expiringTimeout = setTimeout(function(){
				wok.session.flagInTimer = true;
				$("#session-expiring-alert").show();
				$("#session-expiring-alert p").html("<script>var message = i18n['WOKSESS0001M'].replace('%1', 30);"
					+ "$('#session-expiring-alert p').html(message);"
					+ "var n = 30;"
					+ "wok.session.oneSecondExternalCounter = setTimeout(countDown,1000);"
					+ "function countDown(){n--; if(n > 0){wok.session.oneSecondInternalCounter = setTimeout(countDown,1000);}"
					+ "message = i18n['WOKSESS0001M'].replace('%1', n);"
					+ "$('#session-expiring-alert p').html(message);}</script>"
				);
			}, counter);
		}
	},

	refreshExpiringCounter: function() {
		clearTimeout(wok.session.oneSecondExternalCounter);
		clearTimeout(wok.session.oneSecondInternalCounter);
		clearTimeout(wok.session.expiringTimeout);
		wok.session.expiringTimeout = null;
		wok.session.oneSecondExternalCounter = null;
		wok.session.oneSecondInternalCounter = null;
	},

	renewSession: function(){
		wok.getTasks(function(){}, function(){});
		wok.session.flagInTimer = false;
		clearTimeout(wok.session.oneSecondExternalCounter);
		clearTimeout(wok.session.oneSecondInternalCounter);
		wok.session.oneSecondExternalCounter = null;
		wok.session.oneSecondInternalCounter = null;
		$("#session-expiring-alert").hide();
	},

	hideExpiringAlert: function(){
		$("#session-expiring-alert").hide();
	}
};