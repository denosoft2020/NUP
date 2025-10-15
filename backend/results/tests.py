from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import PollingStation, DRForm
from django.urls import reverse


class DRFormModelTest(TestCase):
	def test_create_drform(self):
		station = PollingStation.objects.create(station_id='S1', name='Station 1', district='D1')
		dr = DRForm.objects.create(polling_station=station, sha256_hash='abc123', totals={'NUP': 10})
		self.assertEqual(str(dr.polling_station), 'S1 - Station 1')
		self.assertFalse(dr.verified)


class PublicFeedAPITest(TestCase):
	def setUp(self):
		self.client = Client()
		self.station = PollingStation.objects.create(station_id='S2', name='Station 2', district='D2')
		# create verified and unverified forms
		DRForm.objects.create(polling_station=self.station, sha256_hash='h1', totals={'NUP': 5}, verified=True)
		DRForm.objects.create(polling_station=self.station, sha256_hash='h2', totals={'NUP': 3}, verified=False)

	def test_public_feed_shows_only_verified(self):
		url = reverse('drform-public')
		resp = self.client.get('/api/drforms/public/')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		# only one verified entry
		self.assertEqual(len(data), 1)
