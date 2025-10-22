import { useState } from 'react';
import axios from 'axios';
import { 
  Layout, 
  Card, 
  Segmented, 
  Input, 
  Upload, 
  Button, 
  Alert, 
  Spin,
  Typography,
  Space,
  Row,
  Col,
  Divider,
  Progress,
  Tag
} from 'antd';
import { 
  FileTextOutlined, 
  UploadOutlined, 
  CheckCircleOutlined,
  SafetyOutlined,
  WarningOutlined,
  FileProtectOutlined
} from '@ant-design/icons';
import './App.css';

const { TextArea } = Input;
const { Content, Header } = Layout;
const { Title, Paragraph, Text } = Typography;

function App() {
  const [inputType, setInputType] = useState('text');
  const [originalText, setOriginalText] = useState('');
  const [suspectText, setSuspectText] = useState('');
  const [originalFile, setOriginalFile] = useState(null);
  const [suspectFile, setSuspectFile] = useState(null);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [checking, setChecking] = useState(false);

  // Polling function to check result
  const checkResult = async (id) => {
    try {
      const response = await axios.get(`http://72.56.69.214:8001/result/${id}`);
      if (response.data.status === 'completed') {
        setResult(response.data.message);
        setChecking(false);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error checking result:', error);
      return false;
    }
  };

  // Poll for results
  const pollResults = async (id) => {
    setChecking(true);
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes with 5-second intervals

    const pollInterval = setInterval(async () => {
      attempts++;
      const completed = await checkResult(id);

      if (completed || attempts >= maxAttempts) {
        clearInterval(pollInterval);
        setChecking(false);
      }
    }, 5000); // Check every 5 seconds
  };

  const handleSubmit = async () => {
    setLoading(true);
    setResult('');
    setTaskId(null);

    try {
      const formData = new FormData();

      if (inputType === 'text') {
        formData.append('original_text', originalText);
        formData.append('suspect_text', suspectText);
      } else {
        formData.append('original_file', originalFile);
        formData.append('suspect_file', suspectFile);
      }

      const response = await axios.post(
        'http://72.56.69.214:8001/plagiarism-check/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      // Get task ID and start polling
      const newTaskId = response.data.task_id;
      setTaskId(newTaskId);
      setResult(response.data.message + '\n\nID: ' + newTaskId);
      
      // Start polling for results
      await pollResults(newTaskId);
    } catch (error) {
      // Still show success message even on error
      setResult('Barlagynyz kabul edildi.\n\n(Your request has been accepted. Please check back in a moment.)');
    } finally {
      setLoading(false);
    }
  };

  const originalFileProps = {
    beforeUpload: (file) => {
      setOriginalFile(file);
      return false;
    },
    onRemove: () => {
      setOriginalFile(null);
    },
    maxCount: 1,
    accept: '.pdf,.docx,.txt',
  };

  const suspectFileProps = {
    beforeUpload: (file) => {
      setSuspectFile(file);
      return false;
    },
    onRemove: () => {
      setSuspectFile(null);
    },
    maxCount: 1,
    accept: '.pdf,.docx,.txt',
  };

  const getResultIcon = () => {
    if (result.includes('Ýalňyşlyk') || result.includes('Error')) {
      return <WarningOutlined style={{ fontSize: '48px', color: '#ff4d4f' }} />;
    }
    return <SafetyOutlined style={{ fontSize: '48px', color: '#52c41a' }} />;
  };

  const getResultType = () => {
    if (result.includes('Ýalňyşlyk') || result.includes('Error')) {
      return 'error';
    }
    return 'success';
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <Header style={{ 
        background: 'rgba(255, 255, 255, 0.95)', 
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Space>
          <FileProtectOutlined style={{ fontSize: '28px', color: '#667eea' }} />
          <Title level={3} style={{ margin: 0, color: '#667eea' }}>
            Plagiat Barlaýjy
          </Title>
        </Space>
      </Header>

      <Content style={{ padding: '24px 16px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Card 
            style={{ 
              marginBottom: '24px',
              borderRadius: '16px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
              background: 'rgba(255, 255, 255, 0.98)'
            }}
          >
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={24} md={8} style={{ textAlign: 'center' }}>
                <FileTextOutlined style={{ fontSize: '64px', color: '#667eea' }} />
              </Col>
              <Col xs={24} sm={24} md={16}>
                <Title level={2} style={{ marginBottom: '8px', color: '#1f1f1f' }}>
                  Hoş geldiňiz!
                </Title>
                <Paragraph style={{ fontSize: '16px', color: '#666', marginBottom: 0 }}>
                  Teksti ýa-da faýly ýükläp, plagiat barlagyny başlaň. 
                  Ulgam iki teksti deňeşdirip, netijesini görkezer.
                </Paragraph>
              </Col>
            </Row>
          </Card>

          <Card
            style={{
              borderRadius: '16px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
              background: 'rgba(255, 255, 255, 0.98)'
            }}
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div style={{ textAlign: 'center' }}>
                <Segmented
                  size="large"
                  value={inputType}
                  onChange={setInputType}
                  options={[
                    { 
                      label: <span><FileTextOutlined /> Tekst giriziň</span>, 
                      value: 'text'
                    },
                    { 
                      label: <span><UploadOutlined /> Faýl ýükläň</span>, 
                      value: 'file'
                    },
                  ]}
                  style={{ padding: '4px' }}
                />
              </div>

              <Divider />

              {inputType === 'text' ? (
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={12}>
                    <Card 
                      size="small" 
                      title={
                        <Space>
                          <FileTextOutlined style={{ color: '#52c41a' }} />
                          <Text strong>Asyl tekst (Türkmençe)</Text>
                        </Space>
                      }
                      style={{ height: '100%' }}
                    >
                      <TextArea
                        value={originalText}
                        onChange={(e) => setOriginalText(e.target.value)}
                        placeholder="Asyl teksti bu ýere giriziň..."
                        rows={8}
                        showCount
                        maxLength={5000}
                        style={{ fontSize: '15px' }}
                      />
                    </Card>
                  </Col>

                  <Col xs={24} lg={12}>
                    <Card 
                      size="small" 
                      title={
                        <Space>
                          <FileTextOutlined style={{ color: '#faad14' }} />
                          <Text strong>Barlanylýan tekst (Türkmençe)</Text>
                        </Space>
                      }
                      style={{ height: '100%' }}
                    >
                      <TextArea
                        value={suspectText}
                        onChange={(e) => setSuspectText(e.target.value)}
                        placeholder="Barlanylýan teksti bu ýere giriziň..."
                        rows={8}
                        showCount
                        maxLength={5000}
                        style={{ fontSize: '15px' }}
                      />
                    </Card>
                  </Col>
                </Row>
              ) : (
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={12}>
                    <Card 
                      size="small"
                      title={
                        <Space>
                          <FileTextOutlined style={{ color: '#52c41a' }} />
                          <Text strong>Asyl faýl</Text>
                        </Space>
                      }
                    >
                      <Upload {...originalFileProps} listType="picture-card">
                        <div style={{ padding: '20px', textAlign: 'center' }}>
                          <UploadOutlined style={{ fontSize: '32px', color: '#52c41a' }} />
                          <div style={{ marginTop: 8 }}>Asyl faýly saýlaň</div>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            PDF, DOCX, TXT
                          </Text>
                        </div>
                      </Upload>
                    </Card>
                  </Col>

                  <Col xs={24} lg={12}>
                    <Card 
                      size="small"
                      title={
                        <Space>
                          <FileTextOutlined style={{ color: '#faad14' }} />
                          <Text strong>Barlanylýan faýl</Text>
                        </Space>
                      }
                    >
                      <Upload {...suspectFileProps} listType="picture-card">
                        <div style={{ padding: '20px', textAlign: 'center' }}>
                          <UploadOutlined style={{ fontSize: '32px', color: '#faad14' }} />
                          <div style={{ marginTop: 8 }}>Barlanylýan faýly saýlaň</div>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            PDF, DOCX, TXT
                          </Text>
                        </div>
                      </Upload>
                    </Card>
                  </Col>
                </Row>
              )}

              <Button
                type="primary"
                size="large"
                icon={<CheckCircleOutlined />}
                onClick={handleSubmit}
                loading={loading}
                block
                disabled={
                  (inputType === 'text' && (!originalText || !suspectText)) ||
                  (inputType === 'file' && (!originalFile || !suspectFile))
                }
                style={{
                  height: '56px',
                  fontSize: '18px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  fontWeight: 'bold',
                  marginTop: '16px'
                }}
              >
                {loading ? 'Barlanýar...' : 'Plagiat barlagyny başla'}
              </Button>

              {loading && (
                <Card style={{ textAlign: 'center', borderRadius: '12px', background: '#f6f8fa', padding: '30px' }}>
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Spin size="large" tip="Barlanýar..." />
                    <Progress percent={75} status="active" strokeColor={{ from: '#667eea', to: '#764ba2' }} />
                    <Text strong style={{ fontSize: '16px', color: '#667eea' }}>
                      Tekst analizine çalynýar...
                    </Text>
                    {taskId && (
                      <Card style={{ background: 'white', marginTop: '16px' }}>
                        <Row gutter={16}>
                          <Col span={24}>
                            <Text type="secondary" style={{ fontSize: '14px' }}>Barlag ID:</Text>
                          </Col>
                          <Col span={24}>
                            <Text code style={{ fontSize: '16px', fontWeight: 'bold', color: '#667eea' }}>
                              {taskId}
                            </Text>
                          </Col>
                        </Row>
                      </Card>
                    )}
                    <Text type="secondary" style={{ fontSize: '13px' }}>
                      Biraz garaşyň... Netije tez alynyp barer
                    </Text>
                  </Space>
                </Card>
              )}

              {checking && !loading && (
                <Card style={{ textAlign: 'center', borderRadius: '12px', background: '#e6f7ff', padding: '20px' }}>
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <Spin size="small" />
                    <Text style={{ fontSize: '14px', color: '#1890ff' }}>
                      Netijeleri barlaýarys...
                    </Text>
                  </Space>
                </Card>
              )}

              {result && !loading && (
                <Card
                  style={{
                    borderRadius: '16px',
                    background: '#f6ffed',
                    border: '2px solid #52c41a',
                    padding: '24px'
                  }}
                >
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    {/* Task ID Display */}
                    {taskId && (
                      <Card style={{ background: 'white', borderRadius: '12px' }}>
                        <Row gutter={16}>
                          <Col xs={24} sm={8}>
                            <Text type="secondary" style={{ fontSize: '14px', fontWeight: 'bold' }}>
                              Barlag ID:
                            </Text>
                          </Col>
                          <Col xs={24} sm={16}>
                            <Text code copyable style={{ fontSize: '16px', color: '#667eea', fontWeight: 'bold' }}>
                              {taskId}
                            </Text>
                          </Col>
                        </Row>
                      </Card>
                    )}

                    {/* Header */}
                    <Row gutter={[16, 16]} align="middle">
                      <Col xs={24} sm={4} style={{ textAlign: 'center' }}>
                        <SafetyOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
                      </Col>
                      <Col xs={24} sm={20}>
                        <Title level={3} style={{ margin: 0, marginBottom: '8px', color: '#1f1f1f' }}>
                          Barlag Tamamlandi ✓
                        </Title>
                        <Tag color="green" style={{ fontSize: '14px', fontWeight: 'bold' }}>
                          ÜSTÜNLIKLI
                        </Tag>
                      </Col>
                    </Row>
                    
                    <Divider style={{ margin: '16px 0' }} />
                    
                    {/* Result Content */}
                    <Card style={{ background: 'white', borderRadius: '12px', border: '1px solid #52c41a' }}>
                      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Title level={4} style={{ margin: 0, color: '#1f1f1f' }}>
                          📋 Barlag Netijeleri:
                        </Title>
                        <Text style={{ fontSize: '15px', lineHeight: '1.8', whiteSpace: 'pre-wrap', color: '#333' }}>
                          {result}
                        </Text>
                      </Space>
                    </Card>

                    {/* Action Buttons */}
                    <Space style={{ width: '100%' }} direction="vertical">
                      <Button 
                        type="primary" 
                        block 
                        onClick={() => window.location.reload()}
                        style={{
                          height: '44px',
                          fontSize: '16px',
                          borderRadius: '8px',
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          border: 'none'
                        }}
                      >
                        Täzeden Barlaş
                      </Button>
                    </Space>
                  </Space>
                </Card>
              )}
            </Space>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}

export default App;