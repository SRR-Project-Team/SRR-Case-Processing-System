import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './RegisterForm.css';

const RegisterForm: React.FC = () => {
  // 地址
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  const [isLoading, setIsLoading] = useState(false);

  // 为每个输入框定义对应的状态
  const [formValues, setFormValues] = useState({
    username: '',           // 用户名
    email: '',              // 邮箱
    phone: '',              // 手机号
    password: '',           // 密码
    confirmPassword: ''     // 确认密码
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
    setIsLoading(true)
    // 空值验证
    if (!formValues.username.trim() ||
        !formValues.email.trim() ||
        !formValues.phone.trim() ||
        !formValues.password.trim() ||
        !formValues.confirmPassword.trim()) {
      alert('Please fill in all the information!');
      return;
    }
    // 密码双重验证
    if (formValues.password !== formValues.confirmPassword) {
      alert('Passwords do not match!');
        setFormValues({
          ...formValues,
          password: '',           
          confirmPassword: ''
        });
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
    // 电话验证
    if (formValues.phone.length !== 8) {
      alert('Only 8-digit phone numbers are accepted!');
        setFormValues({
          ...formValues,
          phone : ''
        });
      return;
    }
    registerToBackend()
  };

  // 向后端发送请求
  const registerToBackend = async () => {
    try {
      // 2. 发送POST请求到后端
      const response = await axios.post(`${API_BASE_URL}/user/user-register`, formValues, {
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
        username: '',
        email: '',
        phone: '',
        password: '',
        confirmPassword: ''
      });

      // 跳转到登录页
      window.location.href = '/login';

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
    <div className="register-container">
      {/* 表单标题 */}
      <h2 className="register-title">User Registration</h2>
      
      <form className="register-form">
        {/* 用户名输入框 */}
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input 
            type="text" 
            id="username" 
            className="form-input" 
            placeholder="Username"
            maxLength={10}
            onChange={handleInputChange}
            name='username'
            value={formValues.username}
          />
        </div>

        {/* 邮箱输入框 */}
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input 
            type="email" 
            id="email" 
            className="form-input" 
            placeholder="Email"
            onChange={handleInputChange}
            name='email'
            value={formValues.email}
          />
        </div>

        {/* 电话号码输入框 */}
        <div className="form-group">
          <label htmlFor="phone">Phone-Number (Hong Kong) </label>
          <input 
            type="tel" 
            id="phone" 
            className="form-input" 
            placeholder="Phone-Number"
            onChange={handleInputChange}
            name='phone'
            value={formValues.phone}
          />
        </div>

        {/* 密码输入框 */}
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input 
            type="password" 
            id="password" 
            className="form-input" 
            placeholder="Password"
            onChange={handleInputChange}
            name='password'
            value={formValues.password}
          />
        </div>

        {/* 确认密码输入框 */}
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm-Password</label>
          <input 
            type="password" 
            id="confirmPassword" 
            className="form-input" 
            placeholder="Confirm-Password"
            onChange={handleInputChange}
            name='confirmPassword'
            value={formValues.confirmPassword}
          />
        </div>

        {/* 确认按钮 */}
        <button type="button" className="submit-btn" onClick={handleRegisterClick} disabled={isLoading}>Register</button>

        {/* 登陆界面跳转按钮 */}
        <div className="register-back-to-login">
          <Link to="/login" style={{ textDecoration: 'none', color: 'inherit' }}>
            Log In
          </Link>
        </div>
      </form>
    </div>
  );
};

export default RegisterForm;