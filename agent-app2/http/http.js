let BASE_URL = "";
if (process.env.NODE_ENV === "development") {
	BASE_URL = "http://127.0.0.1:8000";
} else {
	BASE_URL = "https://www.baidu.com";
}

const getAuthHeader = () => {
	const token = uni.getStorageSync("token");
	return {
		"content-type": "application/json",
		"authorization": "Bearer " + token
	};
}

const normalizeError = (statusCode, data) => {
	const error = new Error(data?.detail || data?.message || "请求失败！");
	error.statusCode = statusCode;
	error.data = data;
	return error;
}

const request = (url, options) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: BASE_URL + url,
			header: getAuthHeader(),
			...options,
			success: (res) => {
				const { statusCode, data } = res;
				if (statusCode == 200) {
					if (data && data.result && data.result != "success") {
						reject(normalizeError(statusCode, data));
						return;
					}
					resolve(data);
				} else {
					reject(normalizeError(statusCode, data));
				}
			},
			fail: () => {
				reject(new Error("服务器请求失败！"));
			}
		})
	})
}

const get = (url, data) => {
	let options = { data, method: 'GET' };
	return request(url, options);
}

const post = (url, data) => {
	let options = { data, method: "POST" };
	return request(url, options);
}

const generateName = (data) => {
	const url = "/name"
	return post(url, data);
}

const agentChat = (query, conversationId) => {
	const url = "/agent/chat/stream"
	return post(url, {
		query,
		conversation_id: conversationId
	});
}

const agentChatStream = async (query, handlers = {}, conversationId) => {
	const { onChunk, onComplete, onError } = handlers;
	const url = BASE_URL + "/agent/chat/stream";
	const appendChunk = typeof onChunk === "function" ? onChunk : () => {};
	const finish = typeof onComplete === "function" ? onComplete : () => {};
	const fail = typeof onError === "function" ? onError : () => {};

	try {
		if (typeof fetch === "function" && typeof TextDecoder !== "undefined") {
			const response = await fetch(url, {
				method: "POST",
				headers: getAuthHeader(),
				body: JSON.stringify({
					query,
					conversation_id: conversationId
				})
			});

			if (!response.ok) {
				let errorData = null;
				try {
					errorData = await response.json();
				} catch (e) {
					errorData = { message: await response.text() };
				}
				throw normalizeError(response.status, errorData);
			}

			if (!response.body || !response.body.getReader) {
				const fullText = await response.text();
				appendChunk(fullText);
				finish(fullText);
				return fullText;
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder("utf-8");
			let fullText = "";

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				const chunk = decoder.decode(value, { stream: true });
				if (!chunk) continue;
				fullText += chunk;
				appendChunk(chunk);
			}

			const tail = decoder.decode();
			if (tail) {
				fullText += tail;
				appendChunk(tail);
			}

			finish(fullText);
			return fullText;
		}

		const result = await agentChat(query, conversationId);
		const fullText = typeof result === "string" ? result : JSON.stringify(result);
		appendChunk(fullText);
		finish(fullText);
		return fullText;
	} catch (error) {
		fail(error);
		throw error;
	}
}

const uploadAgentFile = (filePath, name, conversationId) => {
	return new Promise((resolve, reject) => {
		uni.uploadFile({
			url: BASE_URL + "/agent/files/upload",
			filePath,
			name: name || "file",
			formData: {
				conversation_id: conversationId
			},
			header: {
				authorization: getAuthHeader().authorization
			},
			success: (res) => {
				const statusCode = res.statusCode;
				let data = {};
				try {
					data = res.data ? JSON.parse(res.data) : {};
				} catch (e) {
					data = { message: res.data || "上传失败" };
				}
				if (statusCode === 200) {
					resolve(data);
					return;
				}
				reject(normalizeError(statusCode, data));
			},
			fail: () => {
				reject(new Error("文件上传失败！"));
			}
		})
	})
}

const listConversations = () => {
	return get("/agent/conversations");
}

const createConversation = (title = null) => {
	return post("/agent/conversations", title ? { title } : {});
}

const getMessages = (conversationId) => {
	return get(`/agent/conversations/${conversationId}/messages`);
}

const deleteConversation = (conversationId) => {
	return request(`/agent/conversations/${conversationId}`, { method: "DELETE" });
}

const updateConversationTitle = (conversationId, title) => {
	return request(`/agent/conversations/${conversationId}`, {
		method: "PATCH",
		data: { title }
	});
}

const login = (email, password) => {
	let url = "/auth/login";
	return post(url, { email, password });
}

const register = (data) => {
	let url = "/auth/register";
	return post(url, data);
}

const getEmailCode = (email) => {
	let url = "/auth/code"
	return get(url, { email });
}

export default {
	request,
	get,
	post,
	login,
	register,
	getEmailCode,
	generateName,
	agentChat,
	agentChatStream,
	uploadAgentFile,
	listConversations,
	createConversation,
	getMessages,
	deleteConversation,
	updateConversationTitle
}
