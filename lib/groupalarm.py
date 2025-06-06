import requests
from typing import Literal
from typeguard import typechecked
from datetime import datetime


@typechecked
class GroupalarmClient:
	base_url: str = 'https://app.groupalarm.com/api/v1'
	headers = {
		'Accept': 'application/json',
		'Accept-Encoding': 'gzip, deflate, br',
		'Cache-Control': 'no-cache',
		'Connection': 'keep-alive',
	}

	user_id: int
	organization_id: int

	def __init__(self, api_key: str):
		self.api_key = api_key

		self.user_id = None
		self.organization_id = None

	def _get(self, url: str, *, data, **kwargs):
		response = requests.get(f'{self.base_url}/{url}', params=data, headers={
			**self.headers,
			'Personal-Access-Token': self.api_key,
		}, **kwargs)
		try:
			response.raise_for_status()
		except requests.RequestException as e:
			raise ValueError(e) from e
		
		return response.json()
	
	def _post(self, url: str, *, data, **kwargs):
		response = requests.post(f'{self.base_url}/{url}', data=data, headers={
			**self.headers,
			'Personal-Access-Token': self.api_key,
		}, **kwargs)
		try:
			response.raise_for_status()
		except requests.RequestException as e:
			raise ValueError(e) from e
		
		return response.json()
	
	def _put(self, url: str, *, data, **kwargs):
		response = requests.put(f'{self.base_url}/{url}', data=data, headers={
			**self.headers,
			'Personal-Access-Token': self.api_key,
		}, **kwargs)
		try:
			response.raise_for_status()
		except requests.RequestException as e:
			raise ValueError(e) from e
		
		return response.json()
	
	def init(self):
		self.user_id = self.get_user()['id']
		self.organization_id = self.get_organizations()[0]['id']
	
	def get_user(self):
		return self._get('user', data={})

	def get_organizations(self):
		return self._get('organizations', data={})
	
	def get_label(self, label_id: int):
		return self._get(f'label/{label_id}', data={})
	
	def get_appointments(self, *, start: datetime, end: datetime, type: Literal['personal', 'organization'], organization_id: int|None = None):
		if start.tzinfo is None:
			start = start.astimezone()
		if end.tzinfo is None:
			end = end.astimezone()
		if organization_id is None:
			organization_id = self.organization_id
		
		return self._get('appointments/calendar', data={
			'start': start.isoformat(),
			'end': end.isoformat(),
			'type': type,
			'organization_id': organization_id,
		})
	
	def create_appointment(self, *, name: str, description: str, start: datetime, end: datetime, organization_id: int|None = None, label_ids: list[int]|None = None, is_public: bool = False, keep_label_participants_in_sync: bool = True):
		if start.tzinfo is None:
			start = start.astimezone()
		if end.tzinfo is None:
			end = end.astimezone()
		if organization_id is None:
			organization_id = self.organization_id
		
		return self._post('appointment', data={
			'name': name,
			'description': description,
			'startDate': start.isoformat(),
			'endDate': end.isoformat(),
			'organizationID': organization_id,
			'labelIDs': label_ids,
			'isPublic': is_public,
			'keepLabelParticipantsInSync': keep_label_participants_in_sync,
		})
	
	def get_appointment(self, appointment_id: int, *, timestamp: datetime|None = None):
		return self._get(f'appointment/{appointment_id}', data={
			'timestamp': timestamp.isoformat() if timestamp is not None else None,
		})
	
	def get_users(self, *, organization_id: int|None = None):
		if organization_id is None:
			organization_id = self.organization_id
		
		return self._get('users', data={
			'organization': organization_id,
		})

	def get_specific_user(self, user_id: int, *, organization_id: int|None = None):
		if organization_id is None:
			organization_id = self.organization_id
		
		return self._get(f'user/{user_id}', data={
			'organization': organization_id,
		})
