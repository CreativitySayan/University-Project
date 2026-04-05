import React, { useEffect, useRef } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '../../contexts/AuthContext';

export default function AuthCallback() {
  const { session_id } = useLocalSearchParams();
  const router = useRouter();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      if (!session_id) {
        throw new Error('No session_id found');
      }

      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      
      const response = await fetch(BACKEND_URL + '/api/auth/session', {
        method: 'POST',
        headers: {
          'X-Session-ID': session_id as string,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      const userData = await response.json();
      
      const sessionToken = userData.session_token || session_id;
      await AsyncStorage.setItem('session_token', sessionToken as string);
      setUser(userData);
      router.replace('/(tabs)/dashboard');
    } catch (error) {
      console.error('Auth callback error:', error);
      router.replace('/(auth)/login');
    }
  };

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#3B82F6" />
      <Text style={styles.text}>Completing sign in...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  text: {
    color: '#fff',
    fontSize: 16,
  },
});
