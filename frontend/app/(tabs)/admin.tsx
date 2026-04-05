import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function AdminScreen() {
  const [users, setUsers] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'users' | 'logs'>('users');

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');
      
      if (activeTab === 'users') {
        const response = await fetch(BACKEND_URL + '/api/admin/users', {
          headers: {
            'Authorization': 'Bearer ' + sessionToken,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setUsers(data);
        }
      } else {
        const response = await fetch(BACKEND_URL + '/api/admin/logs?limit=50', {
          headers: {
            'Authorization': 'Bearer ' + sessionToken,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setLogs(data);
        }
      }
    } catch (error) {
      console.error('Load data error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const updateRole = async (userId: string, newRole: string) => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');
      
      const response = await fetch(BACKEND_URL + '/api/admin/users/' + userId + '/role?role=' + newRole, {
        method: 'PATCH',
        headers: {
          'Authorization': 'Bearer ' + sessionToken,
        },
      });

      if (response.ok) {
        Alert.alert('Success', 'User role updated');
        loadData();
      }
    } catch (error) {
      console.error('Update role error:', error);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Admin Panel</Text>
      </View>

      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'users' && styles.tabActive]}
          onPress={() => setActiveTab('users')}
        >
          <Ionicons name="people" size={20} color={activeTab === 'users' ? '#3B82F6' : '#64748b'} />
          <Text style={[styles.tabText, activeTab === 'users' && styles.tabTextActive]}>
            Users
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'logs' && styles.tabActive]}
          onPress={() => setActiveTab('logs')}
        >
          <Ionicons name="list" size={20} color={activeTab === 'logs' ? '#3B82F6' : '#64748b'} />
          <Text style={[styles.tabText, activeTab === 'logs' && styles.tabTextActive]}>
            Logs
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3B82F6" />
        }
      >
        {activeTab === 'users' && users.map((user, index) => (
          <UserCard key={index} user={user} onUpdateRole={updateRole} />
        ))}
        {activeTab === 'logs' && logs.map((log, index) => (
          <LogCard key={index} log={log} />
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

function UserCard({ user, onUpdateRole }: any) {
  const [showRoles, setShowRoles] = useState(false);

  return (
    <View style={styles.card}>
      <View style={styles.userHeader}>
        <View>
          <Text style={styles.userName}>{user.name}</Text>
          <Text style={styles.userEmail}>{user.email}</Text>
        </View>
        <TouchableOpacity
          style={styles.roleButton}
          onPress={() => setShowRoles(!showRoles)}
        >
          <Text style={styles.roleText}>{user.role.toUpperCase()}</Text>
          <Ionicons name="chevron-down" size={16} color="#3B82F6" />
        </TouchableOpacity>
      </View>

      {showRoles && (
        <View style={styles.roleOptions}>
          {['admin', 'analyst', 'viewer'].map(role => (
            <TouchableOpacity
              key={role}
              style={[styles.roleOption, user.role === role && styles.roleOptionActive]}
              onPress={() => {
                onUpdateRole(user.user_id, role);
                setShowRoles(false);
              }}
            >
              <Text style={[styles.roleOptionText, user.role === role && styles.roleOptionTextActive]}>
                {role.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

function LogCard({ log }: any) {
  const typeColor = {
    complaint: '#3B82F6',
    prediction: '#10B981',
    alert: '#EF4444',
  }[log.type] || '#64748b';

  return (
    <View style={styles.logCard}>
      <View style={[styles.logIndicator, { backgroundColor: typeColor }]} />
      <View style={styles.logContent}>
        <Text style={styles.logType}>{log.type.toUpperCase()}</Text>
        <Text style={styles.logAction}>{log.action}</Text>
        <Text style={styles.logTime}>
          {new Date(log.timestamp).toLocaleString()}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  header: {
    padding: 16,
    paddingTop: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  tabs: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#1a1a2e',
  },
  tabActive: {
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    borderWidth: 1,
    borderColor: '#3B82F6',
  },
  tabText: {
    fontSize: 14,
    color: '#64748b',
  },
  tabTextActive: {
    color: '#3B82F6',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  card: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  userHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  userEmail: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 2,
  },
  roleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  roleText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3B82F6',
  },
  roleOptions: {
    marginTop: 12,
    gap: 8,
  },
  roleOption: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#0c0c0c',
  },
  roleOptionActive: {
    backgroundColor: '#3B82F6',
  },
  roleOptionText: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
  },
  roleOptionTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  logCard: {
    flexDirection: 'row',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 12,
  },
  logIndicator: {
    width: 4,
  },
  logContent: {
    flex: 1,
    padding: 16,
    gap: 4,
  },
  logType: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3B82F6',
  },
  logAction: {
    fontSize: 14,
    color: '#fff',
  },
  logTime: {
    fontSize: 12,
    color: '#64748b',
  },
});
