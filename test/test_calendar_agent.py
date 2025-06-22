import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the calendar_agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent


class TestCalendarAgent2(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.base_state = {
            "messages": ["테스트 메시지"],
            "agent_messages": []
        }
    
    def test_real_input_classification(self):
        """실제 한국어 입력값으로 분류가 제대로 되는지 테스트"""
        
        # 실제 테스트 케이스들
        test_cases = [
            {
                "input": "내일 오후 2시에 팀 미팅 추가해줘",
                "expected_type": "event",
                "expected_operation": "create",
                "expected_node": "CalC",
                "description": "일정 생성 - 특정 시간"
            },
            {
                "input": "이번 주 일정 보여줘",
                "expected_type": "event", 
                "expected_operation": "read",
                "expected_node": "CalRUD",
                "description": "일정 조회"
            },
            {
                "input": "할일 목록에 장보기 추가해줘",
                "expected_type": "task",
                "expected_operation": "create", 
                "expected_node": "CalC",
                "description": "할일 생성"
            },
            {
                "input": "오늘 할 일 보여줘",
                "expected_type": "task",
                "expected_operation": "read",
                "expected_node": "CalRUD", 
                "description": "할일 조회"
            },
            {
                "input": "내일 미팅을 오후 3시로 수정해줘",
                "expected_type": "event",
                "expected_operation": "update",
                "expected_node": "CalRUD",
                "description": "일정 수정"
            },
            {
                "input": "다음 주 월요일 미팅 삭제해줘",
                "expected_type": "event", 
                "expected_operation": "delete",
                "expected_node": "CalRUD",
                "description": "일정 삭제"
            },
            {
                "input": "이번 주에 보고서 작성해야 해",
                "expected_type": "task",
                "expected_operation": "create",
                "expected_node": "CalC", 
                "description": "할일 생성 - 자연스러운 표현"
            },
            {
                "input": "내일 오전 10시 회의 등록해줘",
                "expected_type": "event",
                "expected_operation": "create",
                "expected_node": "CalC",
                "description": "일정 생성 - 등록 표현"
            },
            {
                "input": "이번 달 일정 확인해줘",
                "expected_type": "event",
                "expected_operation": "read", 
                "expected_node": "CalRUD",
                "description": "일정 조회 - 확인 표현"
            },
            {
                "input": "오늘 장보기 할일 취소해줘",
                "expected_type": "task",
                "expected_operation": "delete",
                "expected_node": "CalRUD",
                "description": "할일 삭제 - 취소 표현"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            with self.subTest(i=i, description=test_case["description"]):
                print(f"\n=== 테스트 {i+1}: {test_case['description']} ===")
                print(f"입력: {test_case['input']}")
                
                # 실제 함수 실행 (모킹 없이)
                test_state = {
                    "messages": [test_case["input"]],
                    "agent_messages": []
                }
                
                try:
                    result = calendar_agent(test_state)
                    
                    print(f"결과 타입: {result.get('calendar_type', 'N/A')}")
                    print(f"결과 작업: {result.get('calendar_operation', 'N/A')}")
                    print(f"다음 노드: {result.get('next_node', 'N/A')}")
                    print(f"추출된 정보: {result.get('extracted_info', {})}")
                    print(f"결과 요약: {result.get('crud_result', 'N/A')}")
                    
                    # 예상 결과와 비교
                    actual_type = result.get('calendar_type', '')
                    actual_operation = result.get('calendar_operation', '')
                    actual_node = result.get('next_node', '')
                    
                    print(f"예상 타입: {test_case['expected_type']} | 실제 타입: {actual_type}")
                    print(f"예상 작업: {test_case['expected_operation']} | 실제 작업: {actual_operation}")
                    print(f"예상 노드: {test_case['expected_node']} | 실제 노드: {actual_node}")
                    
                    # 성공 여부 판단
                    type_match = actual_type == test_case['expected_type']
                    operation_match = actual_operation == test_case['expected_operation']
                    node_match = actual_node == test_case['expected_node']
                    
                    if type_match and operation_match and node_match:
                        print("✅ 모든 예상 결과와 일치!")
                    else:
                        print("❌ 예상 결과와 다름")
                        if not type_match:
                            print(f"   - 타입 불일치: 예상 {test_case['expected_type']}, 실제 {actual_type}")
                        if not operation_match:
                            print(f"   - 작업 불일치: 예상 {test_case['expected_operation']}, 실제 {actual_operation}")
                        if not node_match:
                            print(f"   - 노드 불일치: 예상 {test_case['expected_node']}, 실제 {actual_node}")
                    
                except Exception as e:
                    print(f"❌ 오류 발생: {str(e)}")
                
                print("=" * 50)
    
    @patch('agents.calendar_agent.model')
    def test_event_create_operation(self, mock_model):
        """Test event creation operation classification."""
        # Mock the model response
        mock_response = MagicMock()
        mock_response.content = """{
            "type": "event",
            "operation": "create",
            "extracted_info": {
                "title": "팀 미팅",
                "time": "오후 2시",
                "date": "내일"
            }
        }"""
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["내일 오후 2시에 팀 미팅 추가해줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions
        self.assertEqual(result["calendar_type"], "event")
        self.assertEqual(result["calendar_operation"], "create")
        self.assertEqual(result["next_node"], "CalC")
        self.assertEqual(result["extracted_info"]["title"], "팀 미팅")
        self.assertEqual(result["extracted_info"]["time"], "오후 2시")
        self.assertEqual(result["extracted_info"]["date"], "내일")
        self.assertIn("일정 생성 요청이 분류되었습니다", result["crud_result"])
        
        # Check agent messages
        self.assertEqual(len(result["agent_messages"]), 1)
        self.assertEqual(result["agent_messages"][0]["agent"], "calendar_agent")
    
    @patch('agents.calendar_agent.model')
    def test_task_create_operation(self, mock_model):
        """Test task creation operation classification."""
        # Mock the model response
        mock_response = MagicMock()
        mock_response.content = """{
            "type": "task",
            "operation": "create",
            "extracted_info": {
                "title": "보고서 작성",
                "time": "",
                "date": "이번 주"
            }
        }"""
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["이번 주에 보고서 작성할일 추가해줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions
        self.assertEqual(result["calendar_type"], "task")
        self.assertEqual(result["calendar_operation"], "create")
        self.assertEqual(result["next_node"], "CalC")
        self.assertEqual(result["extracted_info"]["title"], "보고서 작성")
        self.assertIn("할일 생성 요청이 분류되었습니다", result["crud_result"])
    
    @patch('agents.calendar_agent.model')
    def test_event_read_operation(self, mock_model):
        """Test event read operation classification."""
        # Mock the model response
        mock_response = MagicMock()
        mock_response.content = """{
            "type": "event",
            "operation": "read",
            "extracted_info": {
                "title": "",
                "time": "",
                "date": "이번 주"
            }
        }"""
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["이번 주 일정 보여줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions
        self.assertEqual(result["calendar_type"], "event")
        self.assertEqual(result["calendar_operation"], "read")
        self.assertEqual(result["next_node"], "CalRUD")
        self.assertIn("일정 조회 요청이 분류되었습니다", result["crud_result"])
    
    @patch('agents.calendar_agent.model')
    def test_task_read_operation(self, mock_model):
        """Test task read operation classification."""
        # Mock the model response
        mock_response = MagicMock()
        mock_response.content = """{
            "type": "task",
            "operation": "read",
            "extracted_info": {
                "title": "",
                "time": "",
                "date": "오늘"
            }
        }"""
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["오늘 할 일 보여줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions
        self.assertEqual(result["calendar_type"], "task")
        self.assertEqual(result["calendar_operation"], "read")
        self.assertEqual(result["next_node"], "CalRUD")
        self.assertIn("할일 조회 요청이 분류되었습니다", result["crud_result"])
    
    @patch('agents.calendar_agent.model')
    def test_event_update_operation(self, mock_model):
        """Test event update operation classification."""
        # Mock the model response
        mock_response = MagicMock()
        mock_response.content = """{
            "type": "event",
            "operation": "update",
            "extracted_info": {
                "title": "미팅",
                "time": "오후 3시",
                "date": "내일"
            }
        }"""
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["내일 미팅을 오후 3시로 수정해줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions
        self.assertEqual(result["calendar_type"], "event")
        self.assertEqual(result["calendar_operation"], "update")
        self.assertEqual(result["next_node"], "CalRUD")
        self.assertIn("일정 수정 요청이 분류되었습니다", result["crud_result"])
    
    @patch('agents.calendar_agent.model')
    def test_event_delete_operation(self, mock_model):
        """Test event delete operation classification."""
        # Mock the model response
        mock_response = MagicMock()
        mock_response.content = """{
            "type": "event",
            "operation": "delete",
            "extracted_info": {
                "title": "미팅",
                "time": "",
                "date": "내일"
            }
        }"""
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["내일 미팅 삭제해줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions
        self.assertEqual(result["calendar_type"], "event")
        self.assertEqual(result["calendar_operation"], "delete")
        self.assertEqual(result["next_node"], "CalRUD")
        self.assertIn("일정 삭제 요청이 분류되었습니다", result["crud_result"])
    
    @patch('agents.calendar_agent.model')
    def test_default_values_when_missing_fields(self, mock_model):
        """Test that default values are set when classification is missing fields."""
        # Mock the model response with missing fields
        mock_response = MagicMock()
        mock_response.content = """{
            "type": "event"
        }"""
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["일정 보여줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions for default values
        self.assertEqual(result["calendar_type"], "event")
        self.assertEqual(result["calendar_operation"], "read")  # default
        self.assertEqual(result["next_node"], "CalRUD")  # default for read
        self.assertEqual(result["extracted_info"], {})  # default empty dict
    
    @patch('agents.calendar_agent.model')
    def test_error_handling_invalid_json(self, mock_model):
        """Test error handling when model returns invalid JSON."""
        # Mock the model response with invalid JSON
        mock_response = MagicMock()
        mock_response.content = "invalid json response"
        mock_model.invoke.return_value = mock_response
        
        # Test state
        test_state = {
            "messages": ["일정 보여줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions for error handling
        self.assertIn("캘린더 에이전트 2 오류", result["crud_result"])
        self.assertEqual(len(result["agent_messages"]), 1)
        self.assertEqual(result["agent_messages"][0]["agent"], "calendar_agent")
        self.assertIn("error", result["agent_messages"][0])
    
    @patch('agents.calendar_agent.model')
    def test_error_handling_model_exception(self, mock_model):
        """Test error handling when model raises an exception."""
        # Mock the model to raise an exception
        mock_model.invoke.side_effect = Exception("Model connection failed")
        
        # Test state
        test_state = {
            "messages": ["일정 보여줘"],
            "agent_messages": []
        }
        
        # Execute the function
        result = calendar_agent(test_state)
        
        # Assertions for error handling
        self.assertIn("캘린더 에이전트 2 오류", result["crud_result"])
        self.assertIn("Model connection failed", result["crud_result"])
        self.assertEqual(len(result["agent_messages"]), 1)
        self.assertEqual(result["agent_messages"][0]["agent"], "calendar_agent")
        self.assertIn("error", result["agent_messages"][0])
    
    def test_state_preservation(self):
        """Test that existing state is preserved and not overwritten."""
        # Test state with existing data
        test_state = {
            "messages": ["일정 보여줘"],
            "agent_messages": [{"previous": "data"}],
            "existing_key": "existing_value"
        }
        
        with patch('agents.calendar_agent.model') as mock_model:
            # Mock the model response
            mock_response = MagicMock()
            mock_response.content = """{
                "type": "event",
                "operation": "read",
                "extracted_info": {}
            }"""
            mock_model.invoke.return_value = mock_response
            
            # Execute the function
            result = calendar_agent(test_state)
            
            # Assertions for state preservation
            self.assertEqual(result["existing_key"], "existing_value")
            self.assertEqual(len(result["agent_messages"]), 2)  # previous + new
            self.assertEqual(result["agent_messages"][0]["previous"], "data")
    
    @patch('agents.calendar_agent.model')
    def test_real_world_scenarios(self, mock_model):
        """Test various real-world calendar scenarios."""
        test_cases = [
            {
                "input": "내일 오후 3시에 의사 예약 추가해줘",
                "expected_type": "event",
                "expected_operation": "create",
                "expected_node": "CalC"
            },
            {
                "input": "이번 주 할일 목록 보여줘",
                "expected_type": "task", 
                "expected_operation": "read",
                "expected_node": "CalRUD"
            },
            {
                "input": "다음 주 월요일 미팅을 화요일로 변경해줘",
                "expected_type": "event",
                "expected_operation": "update", 
                "expected_node": "CalRUD"
            },
            {
                "input": "오늘 장보기 할일 삭제해줘",
                "expected_type": "task",
                "expected_operation": "delete",
                "expected_node": "CalRUD"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            with self.subTest(i=i):
                # Mock the model response
                mock_response = MagicMock()
                mock_response.content = f"""{{
                    "type": "{test_case['expected_type']}",
                    "operation": "{test_case['expected_operation']}",
                    "extracted_info": {{}}
                }}"""
                mock_model.invoke.return_value = mock_response
                
                # Test state
                test_state = {
                    "messages": [test_case["input"]],
                    "agent_messages": []
                }
                
                # Execute the function
                result = calendar_agent(test_state)
                
                # Assertions
                self.assertEqual(result["calendar_type"], test_case["expected_type"])
                self.assertEqual(result["calendar_operation"], test_case["expected_operation"])
                self.assertEqual(result["next_node"], test_case["expected_node"])

    def test_debug_llm_response(self):
        """LLM 응답을 디버깅하기 위한 테스트"""
        
        test_inputs = [
            "내일 오후 2시에 팀 미팅 추가해줘",
            "이번 주 일정 보여줘",
            "할일 목록에 장보기 추가해줘"
        ]
        
        for i, user_input in enumerate(test_inputs):
            print(f"\n=== 디버깅 테스트 {i+1} ===")
            print(f"입력: {user_input}")
            
            test_state = {
                "messages": [user_input],
                "agent_messages": []
            }
            
            try:
                # calendar_agent 함수의 prompt 부분을 직접 확인
                from agents.calendar_agent import model
                
                prompt = f"""
                다음 질의를 분석하여 일정/할일 관리 작업을 분류해주세요.
                
                [사용자 질의]
                "{user_input}"
                
                **분류 기준:**
                1. **타입 (type):**
                   - "event": 특정 시간에 일어나는 일정 (미팅, 약속, 회의, 파티 등)
                   - "task": 완료해야 할 작업 (보고서 작성, 제출, 준비 등)
                
                2. **작업 (operation):**
                   - "create": 새로운 일정/할일 추가 ("추가", "등록", "만들어", "해야 해" 등)
                   - "read": 기존 일정/할일 조회 ("보여줘", "확인해줘", "뭐야" 등)
                   - "update": 기존 일정/할일 수정 ("수정", "변경", "바꿔" 등)
                   - "delete": 기존 일정/할일 삭제 ("삭제", "취소", "지워" 등)
                
                **예시:**
                - "내일 오후 2시에 팀 미팅 추가해줘" → event, create
                - "이번 주 일정 보여줘" → event, read
                - "할일 목록에 장보기 추가해줘" → task, create
                - "오늘 할 일 보여줘" → task, read
                
                다음 형태로만 응답해주세요 (JSON 형식이 아닌 Python 딕셔너리):
                {{
                    "type": "event",
                    "operation": "create",
                    "extracted_info": {{
                        "title": "추출된 제목",
                        "time": "추출된 시간",
                        "date": "추출된 날짜"
                    }}
                }}
                
                설명이나 추가 텍스트 없이 딕셔너리 포맷의 텍스트로만 응답해주세요.
                """
                
                print(f"프롬프트 전송 중...")
                response = model.invoke(prompt)
                content = response.content.strip()
                
                print(f"LLM 원본 응답:")
                print(f"'{content}'")
                print(f"응답 길이: {len(content)}")
                print(f"응답 타입: {type(content)}")
                
                # 파싱 시도
                import ast
                try:
                    classification = ast.literal_eval(content)
                    print(f"✅ 파싱 성공: {classification}")
                except Exception as parse_error:
                    print(f"❌ 파싱 실패: {parse_error}")
                    
                    # JSON으로 시도
                    import json
                    try:
                        classification = json.loads(content)
                        print(f"✅ JSON 파싱 성공: {classification}")
                    except Exception as json_error:
                        print(f"❌ JSON 파싱도 실패: {json_error}")
                        
                        # 수동으로 정리 시도
                        print("수동 정리 시도...")
                        cleaned_content = content.replace('\n', ' ').replace('```', '').strip()
                        if cleaned_content.startswith('{') and cleaned_content.endswith('}'):
                            try:
                                classification = ast.literal_eval(cleaned_content)
                                print(f"✅ 정리 후 파싱 성공: {classification}")
                            except:
                                print(f"❌ 정리 후에도 파싱 실패")
                
            except Exception as e:
                print(f"❌ 전체 오류: {str(e)}")
            
            print("=" * 50)


if __name__ == '__main__':
    unittest.main()
