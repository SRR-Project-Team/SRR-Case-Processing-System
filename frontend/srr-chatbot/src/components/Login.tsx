import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './Login.css';


const Login: React.FC = () => {

  // 地址
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  const [isLoading, setIsLoading] = useState(false);

  // 为每个输入框定义对应的状态
  const [formValues, setFormValues] = useState({
    email: '',              // 邮箱
    password: '',           // 密码
  });

  // 邮箱正则规则
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  // 接收输入数据
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormValues({
      ...formValues,
      [name]: value
    });
  };

  // 提交操作
  const handleRegisterClick = () => {
    // 空值验证
    if (!formValues.email.trim() || !formValues.password.trim()) {
      alert('Please fill in all the information!');
      return;
    }
    // 邮箱验证
    if (!emailRegex.test(formValues.email)) {
      alert('Incorrect email format!');
        setFormValues({
          ...formValues,
          email : ''
        });
      return;
    }
    user_login()
  };

  // 向后端发送请求
  const user_login = async () => {
    try {
      // 2. 发送POST请求到后端
      const response = await axios.post(`${API_BASE_URL}/user/user-login`, formValues, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 50000
      });

      if (response.data.status === "error"){
        alert(response.data.message)
        return
      }
      console.log('Backend returns data:', response.data);
      
      // 4. 清空表单
      setFormValues({
        email: '',
        password: ''
      });

      // 跳转到登录页
      window.location.href = '/history';

    } catch (error) {
      // 异常处理（后端返回的错误/网络错误）
      let errorMsg = 'Registration failed!';
      // 区分axios错误和普通错误
      if (axios.isAxiosError(error)) {
        // 后端返回的校验错误（如邮箱已注册、手机号格式错误）
        errorMsg = error.response?.data?.detail || error.message;
      }
      alert(errorMsg);
      console.error('Reasons for registration failure：', error);
    } finally {
      // 无论成功/失败，结束加载状态
      setIsLoading(false);
    }
  };

  return (
    <div className="login-form-container">
      <h2 className="login-form-title"> Log In </h2>

      <div className="login-form">
        <div className="login-form-item">
          <label htmlFor="email" className="login-form-label">Email</label>
          <input
            id="email"
            type="email"
            name="email"
            placeholder="Email"
            className="login-form-input"
            onChange={handleInputChange}
            value={formValues.email}
          />
        </div>

        <div className="login-form-item">
          <label htmlFor="password" className="login-form-label">Password</label>
          <input
            id="password"
            type="password"
            name="password"
            placeholder="Password"
            className="login-form-input"
            onChange={handleInputChange}
            value={formValues.password}
          />
        </div>

        <button type="button" className="login-form-submit-btn" onClick={handleRegisterClick} disabled={isLoading}>
          Log In
        </button>
      </div>

      <div className="login-form-register-link">
        <Link to="/register" style={{ textDecoration: 'none', color: 'inherit' }}>
          <span className="login-form-link-text">Register Now</span>
        </Link>
      </div>
    </div>
  );
};

export default Login;