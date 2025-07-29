import json
import datetime
from typing import List, Dict, Optional, Tuple

class TodoItem:
    def __init__(self, title: str, deadline: Optional[datetime.datetime] = None, 
                 priority: int = 3, completed: bool = False,
                 time_block_start: Optional[datetime.datetime] = None,
                 time_block_end: Optional[datetime.datetime] = None):
        self.title = title
        self.deadline = deadline
        self.priority = priority  # 1-5，1最高
        self.completed = completed
        self.time_block_start = time_block_start
        self.time_block_end = time_block_end
        self.id = id(self)  # 简单生成唯一ID

    def to_dict(self) -> Dict:
        """转换为可序列化的字典"""
        return {
            "id": self.id,
            "title": self.title,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "priority": self.priority,
            "completed": self.completed,
            "time_block_start": self.time_block_start.isoformat() if self.time_block_start else None,
            "time_block_end": self.time_block_end.isoformat() if self.time_block_end else None
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """从字典重建对象"""
        return cls(
            title=data["title"],
            deadline=datetime.datetime.fromisoformat(data["deadline"]) if data["deadline"] else None,
            priority=data["priority"],
            completed=data["completed"],
            time_block_start=datetime.datetime.fromisoformat(data["time_block_start"]) if data["time_block_start"] else None,
            time_block_end=datetime.datetime.fromisoformat(data["time_block_end"]) if data["time_block_end"] else None
        )

    def has_time_conflict(self, other: "TodoItem") -> bool:
        """检查与另一个任务的时间块是否冲突"""
        if not self.time_block_start or not self.time_block_end:
            return False
        if not other.time_block_start or not other.time_block_end:
            return False
            
        # 时间重叠检查
        return (self.time_block_start < other.time_block_end and 
                self.time_block_end > other.time_block_start)


class TodoManager:
    def __init__(self, storage_file: str = "todos.json"):
        self.storage_file = storage_file
        self.todos: List[TodoItem] = self.load_todos()

    def load_todos(self) -> List[TodoItem]:
        """从文件加载待办事项"""
        try:
            with open(self.storage_file, "r") as f:
                data = json.load(f)
                return [TodoItem.from_dict(item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_todos(self):
        """保存待办事项到文件"""
        with open(self.storage_file, "w") as f:
            json.dump([todo.to_dict() for todo in self.todos], f, indent=2)

    def add_todo(self, todo: TodoItem) -> bool:
        """添加待办事项，检查时间冲突"""
        # 检查时间冲突
        for existing in self.todos:
            if todo.has_time_conflict(existing):
                print(f"时间冲突！与任务 '{existing.title}' 重叠")
                return False
                
        self.todos.append(todo)
        self.save_todos()
        print("添加成功！")
        return True

    def list_todos(self, sort_by: str = "priority"):
        """列出所有待办事项"""
        if not self.todos:
            print("没有待办事项")
            return

        # 排序键函数
        def get_sort_key(todo: TodoItem):
            if sort_by == "priority":
                return todo.priority
            elif sort_by == "deadline":
                # 没有截止日期的放后面
                return todo.deadline if todo.deadline else datetime.datetime.max
            elif sort_by == "time":
                # 没有时间块的放后面
                return todo.time_block_start if todo.time_block_start else datetime.datetime.max
            return todo.id

        # 排序
        sorted_todos = sorted(
            self.todos,
            key=get_sort_key,
            reverse=sort_by != "priority"  # 优先级高的排前面
        )

        # 打印
        for i, todo in enumerate(sorted_todos, 1):
            status = "✓" if todo.completed else " "
            time_block = f"[{todo.time_block_start.strftime('%H:%M')}-{todo.time_block_end.strftime('%H:%M')}] " if todo.time_block_start else ""
            deadline = f"截止: {todo.deadline.strftime('%Y-%m-%d')} " if todo.deadline else ""
            print(f"{i}. [{status}] {time_block}{todo.title} {deadline}(优先级: {todo.priority})")

    def toggle_complete(self, index: int):
        """标记完成状态（按列表索引）"""
        if 0 <= index < len(self.todos):
            self.todos[index].completed = not self.todos[index].completed
            self.save_todos()
            print("已更新状态")

    def delete_todo(self, index: int):
        """删除待办事项（按列表索引）"""
        if 0 <= index < len(self.todos):
            del self.todos[index]
            self.save_todos()
            print("已删除")


def validate_time_format(time_str: str) -> bool:
    """
    验证时间格式是否正确（HH:MM 格式）
    返回 True 表示格式有效，False 表示无效
    """
    try:
        # 尝试解析时间格式
        datetime.datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def validate_time_block(start_time: str, end_time: str) -> Tuple[bool, str]:
    """
    验证时间块的有效性
    返回 (是否有效, 错误信息)
    """
    # 验证时间格式
    if not validate_time_format(start_time):
        return False, f"开始时间 '{start_time}' 格式无效，请使用 HH:MM 格式（例如 14:30）"
    
    if not validate_time_format(end_time):
        return False, f"结束时间 '{end_time}' 格式无效，请使用 HH:MM 格式（例如 15:30）"
    
    # 解析时间
    try:
        start = datetime.datetime.strptime(start_time, "%H:%M")
        end = datetime.datetime.strptime(end_time, "%H:%M")
    except ValueError as e:
        return False, f"时间解析错误: {str(e)}"
    
    # 检查开始时间是否早于结束时间
    if start >= end:
        return False, "开始时间必须早于结束时间"
    
    # 检查时间块是否过短（至少10分钟）
    time_diff = end - start
    if time_diff.total_seconds() < 600:  # 600秒 = 10分钟
        return False, "时间块长度不能少于10分钟"
    
    return True, "时间块有效"


def parse_datetime(input_str: str, has_time: bool = False) -> Optional[datetime.datetime]:
    """解析用户输入的日期时间（支持多种格式）"""
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%m-%d %H:%M", "%m-%d"]
    if not has_time:
        formats = [f for f in formats if "%" not in f or "H" not in f]
        
    for fmt in formats:
        try:
            return datetime.datetime.strptime(input_str, fmt)
        except ValueError:
            continue
    return None


def main():
    manager = TodoManager()
    print("=== 时间块待办管理器 ===")
    
    while True:
        print("\n命令: add(添加) / list(列表) / complete(完成) / delete(删除) / exit(退出)")
        cmd = input("请输入命令: ").strip().lower()
        
        if cmd == "exit":
            break
            
        elif cmd == "add":
            title = input("任务标题: ").strip()
            if not title:
                print("任务标题不能为空")
                continue
                
            deadline_str = input("截止日期(可选，如2023-12-31): ").strip()
            deadline = parse_datetime(deadline_str) if deadline_str else None
            if deadline_str and not deadline:
                print(f"截止日期 '{deadline_str}' 格式无效，请使用 YYYY-MM-DD 或 MM-DD 格式")
                continue
                
            try:
                priority_input = input("优先级(1-5，1最高，默认3): ").strip()
                priority = int(priority_input) if priority_input else 3
                if not 1 <= priority <= 5:
                    print("优先级必须是1-5之间的数字")
                    continue
            except ValueError:
                print("优先级必须是数字")
                continue
                
            time_block_str = input("时间块（24小时制）(可选，如14:00-15:30): ").strip()
            start, end = None, None
            if time_block_str:
                if "-" not in time_block_str:
                    print("时间块格式无效，请使用 开始时间-结束时间 格式（例如 14:00-15:30）")
                    continue
                    
                s, e = time_block_str.split("-", 1)
                s = s.strip()
                e = e.strip()
                
                # 验证时间块
                is_valid, message = validate_time_block(s, e)
                if not is_valid:
                    print(message)
                    continue
                    
                today = datetime.date.today()
                start = parse_datetime(f"{today} {s}", has_time=True)
                end = parse_datetime(f"{today} {e}", has_time=True)
            
            todo = TodoItem(
                title=title,
                deadline=deadline,
                priority=priority,
                time_block_start=start,
                time_block_end=end
            )
            manager.add_todo(todo)
            
        elif cmd == "list":
            sort_by = input("排序方式(priority/deadline/time): ").strip() or "priority"
            manager.list_todos(sort_by)
            
        elif cmd == "complete":
            try:
                index = int(input("请输入要标记的任务序号: ")) - 1
                manager.toggle_complete(index)
            except ValueError:
                print("请输入数字")
                
        elif cmd == "delete":
            try:
                index = int(input("请输入要删除的任务序号: ")) - 1
                manager.delete_todo(index)
            except ValueError:
                print("请输入数字")
                
        else:
            print("未知命令")


if __name__ == "__main__":
    main()
    