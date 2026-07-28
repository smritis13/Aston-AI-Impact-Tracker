import HttpService from "core/services/Http/HttpService";

export class ChatHttpService {

    
    static async loadConversations({page=1, pageSize=30}) {

        var service = new HttpService();
        var response;

        response = await service.get('/chat/conversation/');

        return response
    }


    static async sendMessage(body:any) {

        var service = new HttpService();
        var response;

        
        response = await service.post('/chat/', body);

        return response;
    }

    static async loadMessages({conversationId='', page=1, pageSize=30}) {

        var service = new HttpService();
        var response;

        response = await service.get(`/chat/conversation/${conversationId}`);


        return response
    }

    
}